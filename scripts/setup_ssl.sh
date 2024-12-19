#!/bin/bash

# Check if domain name is provided
if [ -z "$1" ]; then
    echo "Please provide a domain name"
    echo "Usage: $0 yourdomain.com"
    exit 1
fi

DOMAIN=$1

# Install SSL certificate
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Add SSL renewal to crontab
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -