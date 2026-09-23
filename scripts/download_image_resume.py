#!/usr/bin/env python3
"""OpenHands 镜像按层断点续传下载器(Plan B)

原理: ghcr blob 逐层 curl -C - 续传, 停滞即杀即续, 永不重头;
     完成后组装 docker legacy tarball 并 docker load。
依赖: curl(带 -C -), python3 标准库; 走本机代理 37780。
"""
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request

REPO = "openhands/agent-canvas"
TAG = "1.22.0"
IMAGE = f"ghcr.io/{REPO}:{TAG}"
PROXY = "http://127.0.0.1:37780"
BLOB_DIR = "/tmp/oh-blobs"
OUT_TAR = "/tmp/oh-docker.tar"
ACCEPT = "application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json"


def http_json(url: str, token: str | None = None) -> dict:
    req = urllib.request.Request(url, headers={"Accept": ACCEPT})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    with opener.open(req, timeout=30) as resp:
        return json.load(resp)


def get_token() -> str:
    with urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})) as op:
        with op.open(f"https://ghcr.io/token?scope=repository:{REPO}:pull&service=ghcr.io", timeout=30) as r:
            return json.load(r)["token"]


def curl_resume(url: str, out: str, token: str, expect: int) -> bool:
    """单层下载: curl -C - 续传, 停滞 90s 杀掉重续, 直到 size 达标"""
    attempt = 0
    while os.path.exists(out) and os.path.getsize(out) >= expect and expect > 0:
        return True
    while True:
        attempt += 1
        have = os.path.getsize(out) if os.path.exists(out) else 0
        if expect and have >= expect:
            return True
        print(f"    attempt {attempt}: {have/1048576:.0f}/{expect/1048576:.0f} MB", flush=True)
        p = subprocess.Popen(
            ["curl", "-sS", "-L", "-C", "-", "--max-time", "3600", "--speed-time", "60",
             "--speed-limit", "1024",  # 60s 内 <1KB/s 视为停滞 → 退出码 28
             "-H", f"Authorization: Bearer {token}", "-o", out, url],
            env={**os.environ, "https_proxy": PROXY, "http_proxy": PROXY})
        try:
            rc = p.wait(timeout=3700)
        except subprocess.TimeoutExpired:
            p.kill(); rc = -1
        if rc == 0 and (not expect or os.path.getsize(out) >= expect):
            return True
        time.sleep(3)
        if attempt % 5 == 0:  # token 可能过期, 刷新
            token = get_token()


def main() -> None:
    os.makedirs(BLOB_DIR, exist_ok=True)
    token = get_token()
    print(f"[1] 解析 manifest (via token {token[:12]}...)")
    idx = http_json(f"https://ghcr.io/v2/{REPO}/manifests/{TAG}", token)
    if "manifests" in idx:  # index → 选 amd64
        for m in idx["manifests"]:
            p = m.get("platform", {})
            if p.get("os") == "linux" and p.get("architecture") == "amd64":
                man = http_json(f"https://ghcr.io/v2/{REPO}/manifests/{m['digest']}", token)
                break
        else:
            sys.exit("无 linux/amd64 manifest")
    else:
        man = idx

    layers = [l["digest"] for l in man["layers"]]
    cfg = man["config"]["digest"]
    total = sum(l["size"] for l in man["layers"])
    print(f"[2] 共 {len(layers)} 层 + config, 合计 {total/1048576:.0f} MB")

    # config blob
    cfg_file = f"{BLOB_DIR}/{cfg.split(':')[1]}.config"
    if not os.path.exists(cfg_file):
        curl_resume(f"https://ghcr.io/v2/{REPO}/blobs/{cfg}", cfg_file, token, None)
    shutil.copy(cfg_file, f"{BLOB_DIR}/{cfg.split(':')[1]}")

    for i, l in enumerate(man["layers"], 1):
        digest, size = l["digest"], l["size"]
        name = digest.split(":")[1]
        out = f"{BLOB_DIR}/{name}"
        if os.path.exists(out) and os.path.getsize(out) == size:
            print(f"[3.{i}/{len(layers)}] 已完成, 跳过")
            continue
        print(f"[3.{i}/{len(layers)}] {size/1048576:.0f} MB {digest[:19]}...")
        curl_resume(f"https://ghcr.io/v2/{REPO}/blobs/{digest}", out, token, size)

    print("[4] 组装 docker tarball")
    with tarfile.open(OUT_TAR, "w") as tf:
        for l in man["layers"]:
            tf.add(f"{BLOB_DIR}/{l['digest'].split(':')[1]}", arcname=l["digest"].split(":")[1])
        tf.add(f"{BLOB_DIR}/{cfg.split(':')[1]}", arcname=cfg.split(":")[1])
        manifest_json = json.dumps([{
            "Config": cfg.split(":")[1],
            "RepoTags": [IMAGE],
            "Layers": [d.split(":")[1] for d in layers],
        }])
        import io
        data = manifest_json.encode()
        info = tarfile.TarInfo("manifest.json"); info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    print(f"[5] docker load ({os.path.getsize(OUT_TAR)/1048576:.0f} MB)")
    subprocess.run(["docker", "load", "--input", OUT_TAR], check=True)
    os.remove(OUT_TAR)
    print("OPENHANDS_IMAGE_LOADED")


if __name__ == "__main__":
    main()
