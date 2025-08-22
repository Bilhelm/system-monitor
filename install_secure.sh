#!/bin/bash

# Secure installer for System Monitor with checksum verification
# Author: William Cloutman

set -e  # Exit on any error

echo "📊 Installing System Monitor (Secure Version)..."

# Configuration
REPO="Bilhelm/system-monitor"
FILE="system_monitor.py"
EXPECTED_CHECKSUM="d1d50b659198eb976b74a76765cd1860c7595840ea3d9391c2c0fecabc48e3c5"
INSTALL_DIR="$HOME/bin"
TEMP_FILE="/tmp/${FILE}.tmp"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required. Please install it first.${NC}"
    exit 1
fi

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p ~/Documents/system-reports
mkdir -p ~/Documents/system-monitor-logs

# Download the main script
echo -e "${YELLOW}Downloading System Monitor...${NC}"
if ! curl -sL -o "$TEMP_FILE" "https://raw.githubusercontent.com/${REPO}/master/${FILE}"; then
    echo -e "${RED}❌ Download failed${NC}"
    exit 1
fi

# Verify checksum
echo -e "${YELLOW}Verifying integrity...${NC}"
ACTUAL_CHECKSUM=$(sha256sum "$TEMP_FILE" | cut -d' ' -f1)

if [ "$ACTUAL_CHECKSUM" = "$EXPECTED_CHECKSUM" ]; then
    echo -e "${GREEN}✅ Checksum verified${NC}"
    echo "   Expected: $EXPECTED_CHECKSUM"
    echo "   Actual:   $ACTUAL_CHECKSUM"
else
    echo -e "${RED}❌ Checksum verification failed!${NC}"
    echo "   Expected: $EXPECTED_CHECKSUM"
    echo "   Actual:   $ACTUAL_CHECKSUM"
    echo ""
    echo "This could mean:"
    echo "  1. The file was modified (check for updates)"
    echo "  2. Download was corrupted"
    echo "  3. Potential security issue"
    rm "$TEMP_FILE"
    exit 1
fi

# Install the file
mv "$TEMP_FILE" "$INSTALL_DIR/$FILE"
chmod +x "$INSTALL_DIR/$FILE"

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
if pip3 install --user psutil odfpy 2>/dev/null; then
    echo -e "${GREEN}✅ Dependencies installed${NC}"
elif pip3 install --user --break-system-packages psutil odfpy 2>/dev/null; then
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Could not install dependencies automatically${NC}"
    echo "Please run: pip3 install psutil odfpy"
fi

# Create default config if it doesn't exist
if [ ! -f ~/.system-monitor-config.json ]; then
    echo -e "${YELLOW}Creating default configuration...${NC}"
    cat > ~/.system-monitor-config.json << 'EOF'
{
  "email": {
    "smtp_server": "localhost",
    "smtp_port": 25,
    "from_email": "monitor@localhost",
    "to_emails": ["admin@localhost"],
    "use_authentication": false
  },
  "reports": {
    "output_dir": "~/Documents/system-reports",
    "keep_days": 30
  },
  "monitoring": {
    "check_services": ["ssh", "docker", "nginx", "apache2"],
    "log_files": [
      "/var/log/syslog",
      "/var/log/auth.log"
    ]
  }
}
EOF
    echo -e "${GREEN}✅ Configuration created${NC}"
fi

# Add aliases to bashrc if not already present
if ! grep -q "alias sysmon=" ~/.bashrc 2>/dev/null; then
    echo "alias sysmon='python3 $INSTALL_DIR/$FILE'" >> ~/.bashrc
    echo "alias sysmon-test='python3 $INSTALL_DIR/$FILE --test'" >> ~/.bashrc
    echo "alias sysmon-config='nano ~/.system-monitor-config.json'" >> ~/.bashrc
    echo -e "${GREEN}✅ Added aliases to ~/.bashrc${NC}"
fi

echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "📝 Usage:"
echo "  source ~/.bashrc       # Reload shell configuration"
echo "  sysmon                # Generate system report"
echo "  sysmon-test          # Generate test report"
echo "  sysmon-config        # Edit configuration"
echo ""
echo "⏰ To setup daily reports (8 AM), add to crontab:"
echo "  0 8 * * * python3 $INSTALL_DIR/$FILE --config ~/.system-monitor-config.json"
echo ""
echo "📊 Reports will be saved to: ~/Documents/system-reports/"
echo ""
echo "🔒 This installation was verified using SHA-256 checksum"