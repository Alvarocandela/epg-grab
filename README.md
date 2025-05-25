# XMLTV EPG Merger

A Python tool for downloading, merging, and filtering XMLTV Electronic Program Guide (EPG) files with enhanced PVR compatibility.

## Features

- **Automatic EPG Download**: Download EPG files from configured URLs with automatic compression detection
- **Channel Validation**: Validates that all configured channels exist in their source files and reports missing channels
- **PVR Optimization**: Removes poster images from programmes while preserving channel icons for better PVR compatibility
- **Programme Enhancement**: Standardizes XMLTV formatting (genres, dates, credits, ratings)
- **Multi-language Support**: Properly handles Spanish and other language metadata extraction
- **Cron-Friendly**: Perfect for automated daily EPG updates with logging
- **Smart Compression**: Auto-detects .gz files and decompresses automatically
- **User-Agent Support**: Proper browser headers prevent server blocking
- **Flexible Configuration**: Supports multiple channel filter formats
- **Channel Discovery**: List all available channels across input files

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only standard library)
- Internet connection for EPG downloads

## Installation

```bash
# Clone or download the project
cd epg_grab

# Make scripts executable
chmod +x xmltv_merger.py
chmod +x cron_update_epg.sh
chmod +x setup.sh

# Run setup (creates directories and installs cron job)
./setup.sh
```

## Configuration

### channels.json Format

The main configuration file supports EPG source URLs and channel mappings:

```json
{
  "sources": {
    "source1.xml": {
      "url": "https://example.com/epg1.xml.gz",
      "compression": "auto"
    },
    "source2.xml": "https://example.com/epg2.xml",
  },
  "channels": {
    "Channel1 HD": {
      "source_file": "source1.xml",
      "output_id": "CH1",
      "icon": "https://example.com/channel1-icon.png"
    },
    "Channel2": {
      "source_file": "source2.xml", 
      "output_id": "CH2"
    },
    "Channel3": "source1.xml"
  }
}
```

**Configuration Notes:**
- `sources`: Define EPG download URLs and compression settings
- `channels`: Map channels to their source files with optional custom IDs and icons
- `compression`: Set to "auto" for automatic detection from URL extension
- Short form: `"Channel Name": "source_file.xml"` for simple mappings

## Usage

### Basic Operations

```bash
# Download EPGs and merge channels (default behavior)
python3 xmltv_merger.py

# Download only (no merging)
python3 xmltv_merger.py --download-only

# Skip download and merge existing files
python3 xmltv_merger.py --skip-download

# Force fresh download even if files exist
python3 xmltv_merger.py --force-download

# List all available channels from all sources
python3 xmltv_merger.py --list-channels
```

### Custom Options

```bash
# Custom input/output files
python3 xmltv_merger.py -i xml/*.xml -f channels.json -o merged.xml

# Merge specific files without downloading
python3 xmltv_merger.py -i xml/source1.xml xml/source2.xml -f channels.json --skip-download

# Include all channels (no filtering)
python3 xmltv_merger.py -i xml/*.xml -o all_channels.xml --skip-download
```

### Channel Discovery

Before configuring channels, discover what's available:

```bash
python3 xmltv_merger.py --list-channels
```

This shows all channel IDs, display names, and their source files.

## Legacy Configuration Formats

### Simple JSON Format
```json
{
  "channels": [
    "Channel1 HD",
    "Channel2",
    "Channel3"
  ]
}
```

### Simple Array Format
```json
[
  "Channel1 HD", 
  "Channel2",
  "Channel3"
]
```

### Plain Text Format (channels.txt)
```
Channel1 HD
Channel2  
Channel3
```

## Automated Updates

### Cron Setup

The project includes a cron-ready script for automated daily updates:

```bash
# Install cron job (runs daily at 6 AM)
./setup.sh

# Or manually add to crontab:
0 6 * * * /path/to/epg_grab/cron_update_epg.sh >> /path/to/epg_grab/epg_update.log 2>&1
```

### Logging

The cron script includes automatic logging:
- Daily updates logged to `epg_update.log`
- Log rotation to prevent large files
- Error tracking and notifications

## Channel Validation

The tool validates that all configured channels exist in their source files:

```
Channel Validation Results:
✓ source1.xml: All 5 channels found
✗ source2.xml: 2 of 3 channels found

Missing channels in source2.xml:
- MissingChannel1 
- MissingChannel2

Available channels in source2.xml (sample):
- AvailableChannel1
- AvailableChannel2
- AvailableChannel3
```

## Advanced Configuration Options

When using the advanced JSON format, you can specify:

- **source_file**: Which XML file to get the channel from
- **output_id**: Custom channel ID for the output file  
- **icon**: Custom icon URL for the channel

**Note**: The program automatically removes all `<display-name>` elements from channels in the output file. Only the channel ID (which you can customize with `output_id`) will be used to identify channels.

### Configuration Examples

#### Example 1: Source File Selection and Custom IDs
```json
{
  "channels": {
    "Channel1": {
      "source_file": "source1.xml",
      "output_id": "CH1"
    },
    "Channel2 HD": {
      "source_file": "source2.xml", 
      "output_id": "CH2"
    },
    "Channel3": {
      "source_file": "source1.xml",
      "output_id": "CH3"
    }
  }
}
```

#### Example 2: Simple Source File Selection
```json
{
  "channels": {
    "Channel1": "source1.xml",
    "Channel2 HD": "source2.xml",
    "Channel3": "source1.xml"
  }
}
```

## Command Line Options

- `-i, --input`: Input XMLTV files (supports wildcards, **default: xml/*.xml**)
- `-f, --filter`: Channel filter file (JSON or text format, **default: channels.json**)
- `-o, --output`: Output XMLTV file (**default: combined.xml**)
- `--list-channels`: List all available channels and exit
- `--download-only`: Download EPG files without merging
- `--skip-download`: Skip download and merge existing files only
- `--force-download`: Force fresh download even if files exist

**Note**: With the default settings, you can simply run `python3 xmltv_merger.py` to process all XML files in the xml/ directory using channels.json as the filter and output to combined.xml.

## Examples

### Example 1: Setup and Basic Usage
```bash
# Setup project
./setup.sh

# View available channels
python3 xmltv_merger.py --list-channels

# Create a simple filter file
echo '["Channel1 HD", "Channel2", "Channel3"]' > my_channels.json

# Merge with custom filter
python3 xmltv_merger.py -f my_channels.json -o custom.xml
```

### Example 2: Download and Merge All Channels  
```bash
# Download all EPGs and include all channels (no filtering)
python3 xmltv_merger.py -o all_channels.xml
```

### Example 3: Manual File Processing
```bash
# Process specific files without downloading
python3 xmltv_merger.py -i xml/source1.xml xml/source2.xml -f channels.json --skip-download
```

### Example 4: Cron Job Testing
```bash
# Test cron script manually
./cron_update_epg.sh

# Check logs
tail -f epg_update.log
```

## Output

The merged XMLTV file will contain:
- All specified channels with their metadata (display names, icons, etc.)
- All programme data for the filtered channels with enhanced PVR compatibility
- Proper XMLTV format with UTF-8 encoding
- Standardized programme formatting (genres, dates, credits, ratings)
- Removed poster images from programmes (keeping channel icons)
- Sorted channels and programmes for consistency

## Project Structure

```
epg_grab/
├── xmltv_merger.py        # Main script with download and merge functionality
├── channels.json          # Main configuration file
├── cron_update_epg.sh     # Cron-ready update script with logging
├── setup.sh               # Project setup script
├── combined.xml          # Default output file (generated)
├── epg_update.log        # Update log file (generated)
├── .gitignore            # Git ignore rules
├── README.md             # This documentation
└── xml/                  # Directory for EPG source files (auto-created)
```

## Troubleshooting

### Common Issues

**Missing Channels**: Use `--list-channels` to see available channels and check channel validation output.

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please check the troubleshooting section above or create an issue in the project repository. 
- **Better Error Handling**: Individual file failures won't stop the entire process
- **Auto-Compression**: No need for manual gunzip commands
- **User-Agent Headers**: Fixes 403 errors from some EPG servers
- **Cron-Friendly**: Default behavior perfect for automated updates

**Old workflow:**
```bash
./xml/update_epg.sh
python3 xmltv_merger.py --skip-download
```

**New workflow:**
```bash
python3 xmltv_merger.py
```

## Quick Setup

```bash
# Clone or download the project
git clone <repository-url> epg_grab
cd epg_grab

# Run setup script
./setup.sh
```

The setup script will:
- Make scripts executable
- Create necessary directories
- Test the configuration
- Download initial EPG data
- Display usage instructions
