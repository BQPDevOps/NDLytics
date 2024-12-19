#!/bin/bash

# Install Nginx and Certbot
sudo dnf install -y nginx certbot python3-certbot-nginx

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Create Nginx configuration
sudo tee /etc/nginx/conf.d/ndlytics.conf > /dev/null <<EOL
server {
    listen 80;
    server_name \$host;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOL

# Test and reload Nginx configuration
sudo nginx -t && sudo systemctl reload nginx