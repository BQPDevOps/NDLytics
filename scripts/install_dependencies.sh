#!/bin/bash

# Update package lists
sudo apt-get update -y

# Install Python 3 and pip
sudo apt-get install -y python3 python3-pip

# Navigate to the application directory
cd /home/ec2-user/NDLytics

# Install required Python packages
# pip3 install -r requirements.txt
sed 's/[>=<]=.*//' requirements.txt | xargs -n 1 pip install --prefer-binary
