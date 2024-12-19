#!/bin/bash

# Load environment variables
set -a
source /home/ec2-user/NDLytics/.env
set +a

# AWS ECR repository details
AWS_REGION=${AWS_REGION:-"ap-south-1"}  # Use env variable or default
ECR_REPO_NAME="ndlytics"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO_URI}

# Pull latest image
docker pull ${ECR_REPO_URI}:latest

# Export variables for docker-compose
export AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
export AWS_REGION=${AWS_REGION}

# Stop existing containers and start new ones
cd /home/ec2-user/NDLytics
docker-compose down
docker-compose up -d