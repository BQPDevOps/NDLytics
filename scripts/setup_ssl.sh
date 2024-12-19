#!/bin/bash

# Install certbot
sudo dnf install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx \
    -d ${DOMAIN_NAME} \
    --non-interactive \
    --agree-tos \
    --email ${SSL_EMAIL} \
    --redirect

# Add automatic renewal
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -