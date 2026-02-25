#!/bin/bash

# Bahamas Open Data SSL Setup Script
# This script sets up HTTPS/SSL for bahamasopendata.com

DOMAIN="bahamasopendata.com"
WWW_DOMAIN="www.bahamasopendata.com"
NGINX_CONF="/etc/nginx/sites-available/bahamasopendata"
EMAIL="admin@bahamasopendata.com"

echo "🔒 Bahamas Open Data SSL Setup for $DOMAIN"
echo "=========================================="

# Check if domain resolves correctly
echo "🌐 Checking DNS resolution..."
DOMAIN_IP=$(dig +short $DOMAIN | head -1)
if [ -z "$DOMAIN_IP" ]; then
    echo "⚠️  Warning: DNS not resolving for $DOMAIN"
    echo "   Continuing anyway - certbot will verify..."
else
    echo "✅ DNS resolution: $DOMAIN -> $DOMAIN_IP"
fi

# Test HTTP access
echo "🌍 Testing HTTP access..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN || echo "000")
if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "301" ] && [ "$HTTP_CODE" != "302" ]; then
    echo "⚠️  Warning: HTTP access returned code $HTTP_CODE"
    echo "   Continuing anyway - certbot will verify..."
else
    echo "✅ HTTP access confirmed (code: $HTTP_CODE)"
fi

# Obtain SSL certificate
echo "🔐 Obtaining SSL certificate..."
if sudo certbot --nginx -d $DOMAIN -d $WWW_DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect; then
    echo "✅ SSL certificate obtained successfully"
    
    # Test HTTPS access
    echo "🔒 Testing HTTPS access..."
    sleep 5
    HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN || echo "000")
    if [ "$HTTPS_CODE" = "200" ] || [ "$HTTPS_CODE" = "301" ] || [ "$HTTPS_CODE" = "302" ]; then
        echo "✅ HTTPS access confirmed (code: $HTTPS_CODE)"
        echo ""
        echo "🎉 SSL Setup Complete!"
        echo "Your Bahamas Open Data application is now accessible at:"
        echo "  🔒 https://$DOMAIN"
        echo "  🔒 https://$WWW_DOMAIN"
        echo "  🌐 http://$DOMAIN (redirects to HTTPS)"
        echo ""
    else
        echo "⚠️ SSL certificate installed but HTTPS test returned code: $HTTPS_CODE"
        echo "Please check nginx configuration"
    fi
else
    echo "❌ Failed to obtain SSL certificate"
    echo "Common issues:"
    echo "  - DNS propagation not complete"
    echo "  - Domain not accessible from internet"
    echo "  - Rate limits reached"
    echo "  - Port 80 not accessible from internet"
    echo ""
    echo "You can try again later with: sudo ./setup-ssl.sh"
    exit 1
fi

# Reload nginx
echo "🔄 Reloading nginx..."
sudo systemctl reload nginx

echo ""
echo "🚀 SSL setup completed successfully!"
echo "Bahamas Open Data is now secured with HTTPS at: https://$DOMAIN"
