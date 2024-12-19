#!/bin/bash

# Define the service file path
SERVICE_FILE="/etc/systemd/system/ndlytics.service"

# Create the systemd service file
sudo tee $SERVICE_FILE > /dev/null <<EOL
[Unit]
Description=NDLytics NiceGUI Application
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/NDLytics/app
ExecStart=/usr/bin/python3 /home/ec2-user/NDLytics/app/main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd manager configuration
sudo systemctl daemon-reload