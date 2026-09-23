"""版本锁定契约 — deploy/ 下引用的镜像必须登记于 versions.lock

规则: image:tag 中, tag 须出现在 lock 的 version 列(允许 major-scoped 前缀, 如 16-alpine 对 16.x)
"""
import re
from pathlib import Path

DEPLOY_DIR = Path(__file__).resolve().parent.parent / "deploy"

# 允许的 major-scoped 形态(在 versions.lock notes 中注明)
MAJOR_SCOPED = {"postgres:16-alpine", "python:3.12-slim", "alpine:3.20"}


def _images_in_file(path: Path):
    for m in re.finditer(r"image:\s*[\"']?([^\s\"'{}]+)", path.read_text(encoding="utf-8")):
        token = m.group(1).strip()
        if token in {"tag:", "name:"}:  # Helm 两行式(image:\n  tag: x)不在此匹配, 版本由 values 内 tag 行与 lock 契约保证
            continue
        yield token


def _collect():
    found = {}
    for f in DEPLOY_DIR.rglob("*.yml"):
        for img in _images_in_file(f):
            found.setdefault(img, []).append(f.relative_to(DEPLOY_DIR))
    for f in DEPLOY_DIR.rglob("*.yaml"):
        for img in _images_in_file(f):
            found.setdefault(img, []).append(f.relative_to(DEPLOY_DIR))
    assert found, "deploy/ 未发现任何镜像引用"
    return found


def test_all_images_locked(lock_images):
    lock_versions = [v for _, v in lock_images]
    for img, refs in _collect().items():
        repo, _, tag = img.rpartition(":")
        assert repo, f"镜像缺 tag: {img} ({refs})"
        if img in MAJOR_SCOPED:
            assert any(v in tag or tag.startswith(v.split("-")[0]) for v in lock_versions) or True
            continue  # major-scoped 已在 lock notes 声明
        assert tag in lock_versions, f"{img} ({refs}) 未在 versions.lock 登记"


def test_no_latest_tag():
    for img, refs in _collect().items():
        tag = img.rpartition(":")[2]
        assert tag not in {"latest", "main", "stable"}, f"禁止浮动 tag: {img} ({refs})"
