#!/bin/bash

# Install unzip if not present
sudo dnf install -y unzip

# Download and install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip

# Create AWS credentials directory
mkdir -p ~/.aws

# Create config file
cat > ~/.aws/config <<EOL
[default]
region = ap-south-1
output = json
EOL

# Create credentials file
cat > ~/.aws/credentials <<EOL
[default]
aws_access_key_id = ${AWS_ACCESS_KEY}
aws_secret_access_key = ${AWS_SECRET_KEY}
EOL

# Set proper permissions
chmod 600 ~/.aws/credentials
chmod 600 ~/.aws/config
