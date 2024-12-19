#!/bin/bash

# EC2 instance details
EC2_HOST="your-ec2-ip"
EC2_USER="ec2-user"
KEY_PATH="path/to/your-key.pem"
GITHUB_REPO="https://github.com/your-username/NDLytics.git"

# Copy setup script and env file to EC2
scp -i $KEY_PATH \
    .env \
    scripts/setup_ec2.sh \
    $EC2_USER@$EC2_HOST:/home/ec2-user/NDLytics/

# SSH into EC2 and setup
ssh -i $KEY_PATH $EC2_USER@$EC2_HOST "
    cd /home/ec2-user/NDLytics && \
    chmod +x setup_ec2.sh && \
    ./setup_ec2.sh && \

    # Clone repository
    git clone $GITHUB_REPO . && \

    # Configure AWS credentials
    aws configure set aws_access_key_id ${AWS_ACCESS_KEY_ID} && \
    aws configure set aws_secret_access_key ${AWS_SECRET_ACCESS_KEY} && \
    aws configure set region ${AWS_REGION} && \

    # Build and start the application
    docker-compose up -d --build
"