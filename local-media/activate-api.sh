#!/usr/bin/env bash
set -euo pipefail
bash /mnt/d/project/cv/local-media/sync-runtime.sh
app=/opt/media-app/local-media
python3 -m venv "$app/.venv"
"$app/.venv/bin/python" -m pip install -r "$app/requirements.txt" httpx
cd "$app"
"$app/.venv/bin/python" -m unittest discover -p test_server.py -v

# A passwordless service account runs the HTTP API without root privileges.
id media-app >/dev/null 2>&1 || useradd --system --home-dir /opt/media-app --shell /usr/sbin/nologin media-app
chown -R media-app:media-app "$app/data"
install -d -o media-app -g media-app /opt/media-app/cache /opt/media-app/cache/numba /opt/media-app/cache/torch
# Chatterbox needs writable cache metadata and the language segmenter that was
# downloaded during the verified alice run. Model inference remains offline.
chown -R media-app:media-app /opt/media-models/huggingface
if [ -d /home/alice/.pkuseg ]; then
    cp -a /home/alice/.pkuseg /opt/media-app/.pkuseg
fi
install -d -o media-app -g media-app /opt/media-app/.pkuseg
chown -R media-app:media-app /opt/media-app/.pkuseg
test "$(cat /proc/1/comm)" = systemd
cat > /etc/systemd/system/local-media.service <<'SERVICE'
[Unit]
Description=Local AI media API
After=network.target

[Service]
User=media-app
Group=media-app
WorkingDirectory=/opt/media-app/local-media
ExecStart=/opt/media-app/local-media/run-api.sh
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=HF_HOME=/opt/media-models/huggingface
Environment=NUMBA_CACHE_DIR=/opt/media-app/cache/numba
Environment=TORCH_HOME=/opt/media-app/cache/torch
Environment=XDG_CACHE_HOME=/opt/media-app/cache
Restart=on-failure
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
SERVICE
systemctl daemon-reload
systemctl enable --now local-media
systemctl restart local-media
for attempt in $(seq 1 20); do
    if "$app/.venv/bin/python" -c "import urllib.request,json; r=json.load(urllib.request.urlopen('http://127.0.0.1:8002/health')); assert r['platform']=='linux'; print(r)"; then
        echo UBUNTU_API_VERIFIED
        exit 0
    fi
    sleep 1
done
exit 1
