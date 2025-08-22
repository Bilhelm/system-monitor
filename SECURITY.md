# Security Policy

## Verifying Code Authenticity

This project is maintained by William Cloutman. To ensure you're running authentic, unmodified code:

### 1. Verify File Checksums

Check that downloaded files match the expected checksums:

```bash
# Download the checksums file
curl -O https://raw.githubusercontent.com/Bilhelm/system-monitor/master/checksums.txt

# Verify all files
sha256sum -c checksums.txt
```

Expected checksums (as of last update):
- `system_monitor.py`: d1d50b659198eb976b74a76765cd1860c7595840ea3d9391c2c0fecabc48e3c5
- `test_monitor.py`: e0cf231af87138dd5a72654ab2b6411a34d2b6ae04eb624c1034d743eb18a31f

### 2. Use the Secure Installer

The `install_secure.sh` script includes built-in checksum verification:

```bash
curl -O https://raw.githubusercontent.com/Bilhelm/system-monitor/master/install_secure.sh
chmod +x install_secure.sh
./install_secure.sh
```

### 3. Verify Git Commits (Once GPG is Set Up)

When GPG signing is enabled, verify commits with:

```bash
git log --show-signature
```

## Security Considerations

### Required Permissions

This tool requires certain system permissions to function:

- **Read access to /var/log**: For log analysis
- **Process information access**: Via psutil library
- **Network statistics access**: For connection monitoring
- **Service status queries**: Via systemctl

### What This Tool Does
- ✅ Reads system metrics (CPU, memory, disk, network)
- ✅ Checks service status via systemctl
- ✅ Analyzes log files for errors/warnings
- ✅ Generates local ODF reports
- ✅ Sends email alerts (if configured)

### What This Tool Does NOT Do
- ❌ No data sent to external servers
- ❌ No telemetry or tracking
- ❌ No modification of system configuration
- ❌ No automatic updates
- ❌ No credential storage (except optional SMTP)

### Safe Usage Guidelines

1. **Review the configuration**
   ```bash
   cat ~/.system-monitor-config.json
   ```

2. **Test mode first**
   ```bash
   python3 system_monitor.py --test
   ```

3. **Secure your reports**
   - Reports contain system information
   - Store in protected directories
   - Set appropriate permissions:
   ```bash
   chmod 700 ~/Documents/system-reports
   ```

4. **Email security**
   - Use local SMTP when possible
   - Avoid storing passwords in config
   - Use Thunderbird's built-in security

### Subprocess Calls

This tool makes subprocess calls to:
- `systemctl`: Check service status
- `tail`: Read recent log entries
- `thunderbird`: Open email client

All subprocess calls use explicit commands without shell interpretation to prevent injection attacks.

## Sensitive Data Handling

### What's Collected
- System metrics (non-sensitive)
- Service status
- Log error messages (sanitized)
- Process names (not arguments)

### What's NOT Collected
- Passwords or credentials
- User files or documents
- Browser history
- Personal data
- Command history

### Report Storage
- Reports are stored locally only
- Default location: `~/Documents/system-reports/`
- Automatic cleanup of old reports (configurable)

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email: wcloutman@hotmail.com
3. Include:
   - Description of the issue
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Dependencies

All dependencies are open source:
- `psutil`: Apache License 2.0
- `odfpy`: Apache License 2.0

Regularly update dependencies:
```bash
pip3 install --upgrade psutil odfpy
```

## Audit Log

The tool maintains logs at:
- `~/Documents/system-monitor-logs/`

Review logs regularly for:
- Unexpected errors
- Unusual system metrics
- Failed service checks

## Author

William Cloutman
- Email: wcloutman@hotmail.com
- GitHub: @Bilhelm

---

Last Security Review: August 2025
Next Scheduled Review: February 2026