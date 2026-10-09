#!/usr/bin/env bash
set -euo pipefail

install -d -m 700 /etc/media-app
if [[ ! -f /etc/media-app/tokenhub.env ]]; then
    install -m 600 /opt/media-app/local-media/tokenhub.env.example /etc/media-app/tokenhub.env
fi
install -d -m 755 /etc/systemd/system/local-media.service.d
install -m 644 /opt/media-app/local-media/local-media-tokenhub.conf \
    /etc/systemd/system/local-media.service.d/tokenhub.conf
systemctl daemon-reload
systemctl restart local-media
systemctl is-active --quiet local-media
echo TOKENHUB_SERVICE_CONFIGURED
