#!/bin/bash
# =============================================================
# Haussteuerung – Autostart Setup
# Einmal auf dem Raspberry Pi ausführen:
#   chmod +x setup_autostart.sh
#   sudo ./setup_autostart.sh
# =============================================================

APP_DIR="/home/pi/Haussteuerung"
PYTHON="/usr/bin/python3"
NGROK="/home/pi/bin/ngrok"

echo "==> Erstelle systemd-Service-Dateien..."

# --- 1. daytime.service ---
cat > /etc/systemd/system/daytime.service << EOF
[Unit]
Description=Haussteuerung – Daytime (Rollosteuerung nach Sonnenauf/-untergang)
After=network.target

[Service]
ExecStart=$PYTHON $APP_DIR/daytime.py
WorkingDirectory=$APP_DIR
Restart=on-failure
RestartSec=10
User=pi
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# --- 2. website.service ---
cat > /etc/systemd/system/website.service << EOF
[Unit]
Description=Haussteuerung – Website (lokales Web-Interface, Port 5001)
After=network.target

[Service]
ExecStart=$PYTHON $APP_DIR/website.py
WorkingDirectory=$APP_DIR
Restart=on-failure
RestartSec=10
User=pi
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# --- 3. smarthome.service ---
cat > /etc/systemd/system/smarthome.service << EOF
[Unit]
Description=Haussteuerung – SmartHome (Alexa Flask-Skill, Port 5000)
After=network.target

[Service]
ExecStart=$PYTHON $APP_DIR/SmartHome.py
WorkingDirectory=$APP_DIR
Restart=on-failure
RestartSec=10
User=pi
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# --- 4. ngrok.service ---
cat > /etc/systemd/system/ngrok.service << EOF
[Unit]
Description=Haussteuerung – ngrok Tunnel (SmartHome statisch + Website mit Google OAuth)
After=network.target smarthome.service website.service
Wants=smarthome.service website.service

[Service]
ExecStart=$NGROK start --all --config $APP_DIR/ngrok.yml
WorkingDirectory=$APP_DIR
Restart=on-failure
RestartSec=15
User=pi
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "==> Lade systemd neu..."
systemctl daemon-reload

echo "==> Aktiviere Services (Autostart bei Boot)..."
systemctl enable daytime.service
systemctl enable website.service
systemctl enable smarthome.service
systemctl enable ngrok.service

echo "==> Starte Services jetzt..."
systemctl start daytime.service
systemctl start website.service
systemctl start smarthome.service
sleep 3   # kurz warten bis Flask-Apps laufen
systemctl start ngrok.service

echo ""
echo "==> Fertig! Status-Überblick:"
echo "------------------------------------------------------------"
systemctl status daytime website smarthome ngrok --no-pager -l
echo ""
echo "Nützliche Befehle:"
echo "  sudo systemctl status daytime website smarthome ngrok"
echo "  sudo journalctl -u website -f        (Live-Log Website)"
echo "  sudo journalctl -u smarthome -f      (Live-Log SmartHome)"
echo "  sudo journalctl -u daytime -f        (Live-Log Daytime)"
echo "  sudo systemctl restart smarthome     (Service neu starten)"
