#!/usr/bin/env bash
set -euo pipefail

install -d -m 700 /etc/media-app
if [[ ! -f /etc/media-app/truthscan.env ]]; then
    install -m 600 /opt/media-app/local-media/truthscan.env.example /etc/media-app/truthscan.env
fi
install -d -m 755 /etc/systemd/system/local-media.service.d
install -m 644 /opt/media-app/local-media/local-media-truthscan.conf \
    /etc/systemd/system/local-media.service.d/truthscan.conf
systemctl daemon-reload
systemctl restart local-media
systemctl is-active --quiet local-media
echo TRUTHSCAN_SERVICE_CONFIGURED
