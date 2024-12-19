#!/bin/bash

# EC2 instance details
EC2_HOST="ec2-44-206-20-29.compute-1.amazonaws.com"
EC2_USER="ec2-user"
KEY_PATH="/Users/chrisortiz/.ssh/NDLytics.pem"

# Copy updated Nginx config if needed
scp -i $KEY_PATH \
    scripts/install_nginx.sh \
    $EC2_USER@$EC2_HOST:/home/ec2-user/NDLytics/

# SSH into EC2 and update
ssh -i $KEY_PATH $EC2_USER@$EC2_HOST "
    cd /home/ec2-user/NDLytics && \

    # Pull latest changes
    git pull && \

    # Update Nginx if config changed
    source .env && \
    ./install_nginx.sh && \

    # Rebuild and restart
    docker-compose down
    docker-compose up -d --build
"