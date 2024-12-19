#!/bin/bash

# Reload systemd manager configuration
sudo systemctl daemon-reload

# Start the NDLytics service
sudo systemctl start ndlytics.service

# Enable the service to start on boot
sudo systemctl enable ndlytics.service