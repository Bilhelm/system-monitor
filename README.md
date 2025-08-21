# System Monitor & Report Generator 📊

A FOSS system monitoring tool for Ubuntu/Linux that generates LibreOffice-compatible reports and integrates with Thunderbird for email alerts.

## Features

- **Comprehensive Monitoring**
  - CPU, Memory, Disk usage tracking
  - Network statistics
  - Process monitoring
  - Service status checking
  - System log analysis
  - Temperature monitoring (if available)

- **Smart Alerting**
  - Configurable thresholds
  - Automatic alert detection
  - Email notifications via Thunderbird

- **Professional Reports**
  - LibreOffice Writer compatible (ODF format)
  - Detailed system metrics
  - Historical tracking
  - Clean, readable formatting

- **100% FOSS**
  - Works with Thunderbird email
  - Generates LibreOffice documents
  - No proprietary dependencies
  - Perfect for Ubuntu/Linux

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Bilhelm/system-monitor.git
cd system-monitor
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Test the installation:
```bash
python3 system_monitor.py --test
```

## Usage

### Manual Report Generation
```bash
python3 system_monitor.py
```

### Configure for Daily Reports
```bash
# Setup cron job (runs daily at 8 AM)
python3 system_monitor.py --setup-cron
```

Then add the displayed line to your crontab:
```bash
crontab -e
```

### Custom Configuration

Create a `config.json` file:
```json
{
  "email": {
    "smtp_server": "localhost",
    "smtp_port": 25,
    "from_email": "monitor@yourdomain.com",
    "to_emails": ["admin@yourdomain.com"],
    "use_authentication": false
  },
  "reports": {
    "output_dir": "/home/user/Documents/system-reports",
    "keep_days": 30
  },
  "monitoring": {
    "check_services": ["ssh", "docker", "nginx"],
    "log_files": [
      "/var/log/syslog",
      "/var/log/auth.log"
    ]
  }
}
```

Run with custom config:
```bash
python3 system_monitor.py --config config.json
```

## Thunderbird Integration

### Option 1: Direct SMTP
Configure Thunderbird with an SMTP server, then the tool can send directly.

### Option 2: Compose Window
If SMTP isn't configured, the tool opens emails in Thunderbird for manual sending.

## Report Output

Reports are saved as `.odt` files in:
- Default: `~/Documents/system-reports/`
- Custom: Configure in `config.json`

Open reports with LibreOffice Writer:
```bash
libreoffice ~/Documents/system-reports/system_report_*.odt
```

## Alert Thresholds

Default thresholds (customizable in code):
- CPU: 80%
- Memory: 85%
- Disk: 90%
- Temperature: 80°C

## Example Report Contents

- System overview and uptime
- CPU usage and load averages
- Memory and swap usage
- Disk usage by partition
- Network statistics
- Top processes by CPU/memory
- Service status
- Recent log errors/warnings
- Authentication failures

## Testing

Run the test suite:
```bash
python3 test_monitor.py
```

## Requirements

- Python 3.6+
- Ubuntu/Linux system
- LibreOffice (for viewing reports)
- Thunderbird (optional, for email)

## Value Proposition

- **For Small Business**: Professional monitoring without expensive licenses
- **For IT Teams**: Automated daily health reports
- **For System Admins**: Early warning system for issues
- **Cost Savings**: Replaces tools that cost $100s-$1000s/month

## Security Note

- Requires sudo/root access for some system metrics
- Log analysis requires read access to /var/log
- Email credentials should be stored securely

## Contributing

Pull requests welcome! This is a FOSS project focused on Ubuntu/Linux compatibility.

## License

MIT License - Free for personal and commercial use

## Author

William Cloutman (wcloutman@hotmail.com)