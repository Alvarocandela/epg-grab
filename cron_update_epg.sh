#!/bin/bash
# EPG Grabber Cron Job Example
# 
# This script downloads fresh EPG data and merges it according to your channel configuration.
# Perfect for automated daily EPG updates via cron.
#
# Example crontab entry (runs daily at 6 AM):
# 0 6 * * * /path/to/your/epg_grab/cron_update_epg.sh
#
# Example crontab entry (runs twice daily at 6 AM and 6 PM):
# 0 6,18 * * * /path/to/your/epg_grab/cron_update_epg.sh

# Change to the script directory
cd "$(dirname "$0")"

# Set up logging with rotation
LOG_FILE="epg_update.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Rotate log file if it gets too large (>1MB)
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || echo 0) -gt 1048576 ]; then
    mv "$LOG_FILE" "${LOG_FILE}.old"
fi

echo "[$DATE] Starting EPG update..." >> "$LOG_FILE"

# Run the EPG merger with forced download (default behavior)
# This will:
# 1. Download fresh EPG data from all configured sources
# 2. Auto-detect compression from file extensions
# 3. Merge and filter channels according to channels.json
# 4. Generate combined.xml output
python3 xmltv_merger.py >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$DATE] EPG update completed successfully" >> "$LOG_FILE"
    
    # Optional: Check output file size as a sanity check
    if [ -f "combined.xml" ]; then
        SIZE=$(ls -lh combined.xml | awk '{print $5}')
        echo "[$DATE] Generated combined.xml ($SIZE)" >> "$LOG_FILE"
    fi
else
    echo "[$DATE] EPG update failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "[$DATE] EPG update finished" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

exit $EXIT_CODE
