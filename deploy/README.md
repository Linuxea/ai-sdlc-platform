# deploy/
各组件部署配置: docker-compose(本地冒烟) + Helm values(K8s)。
版本一律引用根目录 versions.lock, 禁止 latest。密钥经 .env / Secret 注入。
