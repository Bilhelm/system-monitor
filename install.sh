#!/bin/bash

# System Monitor - One-line installer
echo "📊 Installing System Monitor..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install it first."
    exit 1
fi

# Create directories
mkdir -p ~/bin
mkdir -p ~/Documents/system-reports
mkdir -p ~/Documents/system-monitor-logs

# Download the main script
echo -e "${YELLOW}Downloading System Monitor...${NC}"
curl -o ~/bin/system_monitor.py https://raw.githubusercontent.com/Bilhelm/system-monitor/master/system_monitor.py
chmod +x ~/bin/system_monitor.py

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip3 install --user --break-system-packages psutil odfpy 2>/dev/null || pip3 install --user psutil odfpy

# Create default config
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

# Add alias to bashrc
if ! grep -q "alias sysmon=" ~/.bashrc; then
    echo "alias sysmon='python3 ~/bin/system_monitor.py'" >> ~/.bashrc
    echo "alias sysmon-test='python3 ~/bin/system_monitor.py --test'" >> ~/.bashrc
    echo "alias sysmon-config='nano ~/.system-monitor-config.json'" >> ~/.bashrc
fi

# Create desktop launcher (optional)
if [ -d ~/.local/share/applications ]; then
    cat > ~/.local/share/applications/system-monitor.desktop << 'EOF'
[Desktop Entry]
Name=System Monitor Report
Comment=Generate system health report
Exec=python3 ~/bin/system_monitor.py --test
Icon=utilities-system-monitor
Terminal=true
Type=Application
Categories=System;Monitor;
EOF
fi

echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "📝 Usage:"
echo "  sysmon        - Generate system report"
echo "  sysmon-test   - Generate test report"
echo "  sysmon-config - Edit configuration"
echo ""
echo "🔄 To activate aliases, run:"
echo "  source ~/.bashrc"
echo ""
echo "⏰ To setup daily reports (8 AM), add to crontab:"
echo "  0 8 * * * python3 ~/bin/system_monitor.py --config ~/.system-monitor-config.json"
echo ""
echo "📊 Reports will be saved to: ~/Documents/system-reports/"