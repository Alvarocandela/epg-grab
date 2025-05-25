#!/bin/bash
# EPG Grabber Setup Script
# This script sets up the EPG grabber for first-time use

echo "🔧 Setting up EPG Grabber..."

# Make scripts executable
chmod +x xmltv_merger.py
chmod +x cron_update_epg.sh

echo "✅ Made scripts executable"

# Create xml directory if it doesn't exist
mkdir -p xml

echo "✅ Created xml directory"

# Test the configuration
echo "🧪 Testing configuration..."
python3 xmltv_merger.py --download-only

if [ $? -eq 0 ]; then
    echo "✅ Configuration test passed - EPG sources downloaded successfully"
else
    echo "❌ Configuration test failed - please check your channels.json"
    exit 1
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📖 Usage:"
echo "  Manual run:    ./xmltv_merger.py"
echo "  Cron script:   ./cron_update_epg.sh"
echo ""
echo "📅 To set up daily cron job (6 AM):"
echo "  crontab -e"
echo "  Add: 0 6 * * * $(pwd)/cron_update_epg.sh"
echo ""
echo "📁 Files:"
echo "  - channels.json     Configuration (sources and channel filters)"
echo "  - combined.xml      Output file (merged EPG data)"
echo "  - epg_update.log    Log file (created by cron jobs)"
echo "  - xml/              Downloaded EPG source files"
