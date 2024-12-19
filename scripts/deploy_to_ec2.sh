#!/bin/bash

# EC2 instance details
EC2_HOST="ec2-44-206-20-29.compute-1.amazonaws.com"
EC2_USER="ec2-user"
KEY_PATH="/Users/chrisortiz/.ssh/NDLytics.pem"
GITHUB_REPO="https://github.com/BQPDevOps/NDLytics.git"

# Copy setup script and env file to EC2
scp -i $KEY_PATH \
    .env \
    scripts/setup_ec2.sh \
    scripts/install_nginx.sh \
    scripts/setup_ssl.sh \
    $EC2_USER@$EC2_HOST:/home/ec2-user/NDLytics/

# SSH into EC2 and setup
ssh -i $KEY_PATH $EC2_USER@$EC2_HOST "
    mkdir -p /home/ec2-user/NDLytics && \
    cd /home/ec2-user/NDLytics && \

    # Remove existing contents if any
    rm -rf * && \

    # Clone repository
    git clone $GITHUB_REPO . && \

    # Then copy and make scripts executable
    chmod +x *.sh && \

    # Run setup scripts
    ./setup_ec2.sh && \

    # Configure AWS credentials
    aws configure set aws_access_key_id ${AWS_ACCESS_KEY_ID} && \
    aws configure set aws_secret_access_key ${AWS_SECRET_ACCESS_KEY} && \
    aws configure set region ${AWS_REGION} && \

    # Setup Nginx and SSL
    source .env && \
    ./install_nginx.sh && \
    ./setup_ssl.sh && \

    # Build and start the application
    docker-compose up -d --build
"