#!/bin/bash

# Load environment variables
set -a
source /home/ec2-user/NDLytics/.env
set +a

cd /home/ec2-user/NDLytics
docker-compose up -d