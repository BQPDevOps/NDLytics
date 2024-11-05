#!/bin/bash

# Reload systemd manager configuration
sudo systemctl daemon-reload

# Restart the NDLytics service
sudo systemctl restart NDLytics.service

# Enable the service to start on boot
sudo systemctl enable NDLytics.service
