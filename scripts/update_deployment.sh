#!/bin/bash

# EC2 instance details
EC2_HOST="your-ec2-ip"
EC2_USER="ec2-user"
KEY_PATH="path/to/your-key.pem"

# SSH into EC2 and update
ssh -i $KEY_PATH $EC2_USER@$EC2_HOST "
    cd /home/ec2-user/NDLytics && \

    # Pull latest changes
    git pull && \

    # Rebuild and restart
    docker-compose down
    docker-compose up -d --build
"