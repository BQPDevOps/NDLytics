#!/bin/bash

# EC2 instance details
EC2_HOST="ec2-44-206-20-29.compute-1.amazonaws.com"
EC2_USER="ec2-user"
KEY_PATH="/Users/chrisortiz/.ssh/NDLytics.pem"

# SSH into EC2 and show logs
ssh -i $KEY_PATH $EC2_USER@$EC2_HOST "
    cd /home/ec2-user/NDLytics && \
    docker-compose logs -f
"