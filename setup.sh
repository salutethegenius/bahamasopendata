#!/bin/bash

# Setup script for Bahamas Open Data
echo "🚀 Setting up Bahamas Open Data..."

# Navigate to apps directory
cd /home/ubuntu/apps

# Clone the repository if it doesn't exist
if [ ! -d "bahamasopendata/.git" ]; then
    echo "📥 Cloning repository..."
    if [ -d "bahamasopendata" ] && [ "$(ls -A bahamasopendata 2>/dev/null | grep -v -E 'setup.sh|deploy.sh|nginx.conf')" ]; then
        echo "⚠️  Directory exists with files, skipping clone"
    else
        # Remove directory if it only has our setup files
        if [ -d "bahamasopendata" ]; then
            cd bahamasopendata
            # Backup our setup files
            cp setup.sh /tmp/bahamasopendata-setup.sh 2>/dev/null || true
            cp deploy.sh /tmp/bahamasopendata-deploy.sh 2>/dev/null || true
            cp nginx.conf /tmp/bahamasopendata-nginx.conf 2>/dev/null || true
            cd ..
            rm -rf bahamasopendata
        fi
        git clone https://github.com/salutethegenius/bahamasopendata.git
        # Restore setup files
        if [ -f /tmp/bahamasopendata-setup.sh ]; then
            cp /tmp/bahamasopendata-setup.sh bahamasopendata/setup.sh
            cp /tmp/bahamasopendata-deploy.sh bahamasopendata/deploy.sh
            cp /tmp/bahamasopendata-nginx.conf bahamasopendata/nginx.conf
            chmod +x bahamasopendata/setup.sh bahamasopendata/deploy.sh
        fi
    fi
fi

cd bahamasopendata

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
if [ -f "frontend/package.json" ]; then
    cd frontend
    npm install
    echo "🔨 Building frontend..."
    npm run build
    cd ..
fi

# Check if .env file exists, create example if not
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "📝 Copying .env.example to .env..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
fi

echo "✅ Setup complete!"
echo "📝 Next steps:"
echo "   1. Update .env file if needed"
echo "   2. Run: pm2 restart ecosystem.config.js"
echo "   3. Configure nginx (see nginx.conf)"
