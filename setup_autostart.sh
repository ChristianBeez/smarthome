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

# --- 5. hello_task.service ---
cat > /etc/systemd/system/hello_task.service << EOF
[Unit]
Description=Hello Task – schreibt 'hallo' um 03:30 Uhr

[Service]
Type=oneshot
User=pi
WorkingDirectory=$APP_DIR
ExecStart=$PYTHON $APP_DIR/hello_task.py
StandardOutput=journal
StandardError=journal
EOF

# --- 6. hello_task.timer ---
cat > /etc/systemd/system/hello_task.timer << EOF
[Unit]
Description=Täglich um 03:30 Uhr 'hallo' ausgeben

[Timer]
OnCalendar=*-*-* 03:30:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "==> Lade systemd neu..."
systemctl daemon-reload

echo "==> Aktiviere Services (Autostart bei Boot)..."
systemctl enable daytime.service
systemctl enable website.service
systemctl enable smarthome.service
systemctl enable ngrok.service
systemctl enable hello_task.timer

echo "==> Starte Services jetzt..."
systemctl start daytime.service
systemctl start website.service
systemctl start smarthome.service
sleep 3   # kurz warten bis Flask-Apps laufen
systemctl start ngrok.service
systemctl start hello_task.timer

echo ""
echo "==> Fertig! Status-Überblick:"
echo "------------------------------------------------------------"
systemctl status daytime website smarthome ngrok hello_task.timer --no-pager -l
echo ""
echo "Nützliche Befehle:"
echo "  sudo systemctl status daytime website smarthome ngrok hello_task.timer"
echo "  sudo journalctl -u website -f        (Live-Log Website)"
echo "  sudo journalctl -u smarthome -f      (Live-Log SmartHome)"
echo "  sudo journalctl -u daytime -f        (Live-Log Daytime)"
echo "  sudo journalctl -u hello_task -f     (Live-Log Hello Task)"
echo "  sudo systemctl restart smarthome     (Service neu starten)"
echo "  systemctl list-timers hello_task.timer  (nächste Ausführung)"
