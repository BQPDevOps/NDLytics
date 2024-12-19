#!/bin/bash

# Check if the NDLytics service is active
SERVICE_STATUS=$(systemctl is-active ndlytics.service)

if [ "$SERVICE_STATUS" != "active" ]; then
  echo "NDLytics service is not running."
  exit 1
else
  echo "NDLytics service is running."
  exit 0
fi