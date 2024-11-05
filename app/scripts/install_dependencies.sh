#!/bin/bash

# Update the package list
sudo yum update -y

# Install Python 3 and pip
sudo yum install -y python3 python3-pip

# Install virtualenv
sudo pip3 install virtualenv

# Navigate to the application directory
cd /home/NDLytics/app || exit

# Create a virtual environment
virtualenv venv

# Activate the virtual environment
source venv/bin/activate

# Install application dependencies
pip install -r requirements.txt

# Deactivate the virtual environment
deactivate
