#!/bin/bash

# Load environment variables
set -a
source .env
set +a

# AWS ECR repository details
AWS_REGION=${AWS_REGION:-"ap-south-1"}
ECR_REPO_NAME="ndlytics"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"

# Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names ${ECR_REPO_NAME} || \
    aws ecr create-repository --repository-name ${ECR_REPO_NAME}

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO_URI}

# Build and push using docker-compose
docker-compose build
docker-compose push

echo "Image pushed to: ${ECR_REPO_URI}:latest"