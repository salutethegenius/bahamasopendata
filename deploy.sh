#!/bin/bash

# Deployment script for Bahamas Open Data
echo "🚀 Deploying Bahamas Open Data..."

# Run setup
cd /home/ubuntu/apps/bahamasopendata
chmod +x setup.sh
./setup.sh

# Install nginx config
echo "⚙️  Installing nginx configuration..."
sudo cp nginx.conf /etc/nginx/sites-available/bahamasopendata
sudo ln -sf /etc/nginx/sites-available/bahamasopendata /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

# Start/restart with PM2
echo "🚀 Starting application with PM2..."
cd /home/ubuntu/apps
pm2 restart ecosystem.config.js --update-env || pm2 start ecosystem.config.js --env production
pm2 save

echo "✅ Deployment complete!"
echo "🌐 Site should be accessible at http://bahamasopendata.com"
echo "📊 Check status: pm2 status"
echo "📝 View logs: pm2 logs bahamasopendata"
