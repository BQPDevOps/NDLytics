#!/bin/bash

# Update package lists
sudo apt-get update -y

# Install Python 3 and pip
sudo apt-get install -y python3 python3-pip python3-venv

# Navigate to the application directory
cd /home/ec2-user/NDLytics

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip within the virtual environment
pip install --upgrade pip

# Install required Python packages
pip install -r requirements.txt

# Deactivate the virtual environment
deactivate