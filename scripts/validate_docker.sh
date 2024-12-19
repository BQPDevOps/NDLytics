#!/bin/bash

cd /home/ec2-user/NDLytics

# Check if containers are running
if docker-compose ps --services --filter "status=running" | grep ndlytics; then
    echo "Docker containers are running"
    exit 0
else
    echo "Docker containers are not running"
    docker-compose logs
    exit 1
fi