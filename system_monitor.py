#!/usr/bin/env python3
"""
System Monitor & Report Generator
Generates system health reports in ODF format for LibreOffice
Sends alerts via Thunderbird email
Author: William Cloutman
"""

import os
import json
import psutil
import socket
import platform
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from typing import Dict, List
try:
    from typing import List, Dict
except ImportError:
    List = list
    Dict = dict

# ODF (OpenDocument Format) generation
from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties
from odf.text import H, P, List, ListItem

class SystemMonitor:
    """Monitor system health and generate reports."""
    
    def __init__(self, config_path: str = None):
        """Initialize the system monitor."""
        self.hostname = socket.gethostname()
        self.system = platform.system()
        self.config = self.load_config(config_path)
        self.setup_logging()
        
        # Thresholds for alerts
        self.thresholds = {
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90,
            'temp_celsius': 80
        }
        
    def load_config(self, config_path: str = None) -> dict:
        """Load configuration from file or create default."""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            'email': {
                'smtp_server': 'localhost',  # Thunderbird local SMTP
                'smtp_port': 25,
                'from_email': 'monitor@localhost',
                'to_emails': ['admin@localhost'],
                'use_authentication': False
            },
            'reports': {
                'output_dir': str(Path.home() / 'Documents' / 'system-reports'),
                'keep_days': 30
            },
            'monitoring': {
                'check_services': ['ssh', 'docker', 'nginx', 'apache2'],
                'log_files': [
                    '/var/log/syslog',
                    '/var/log/auth.log',
                    '/var/log/kern.log'
                ]
            }
        }
    
    def setup_logging(self):
        """Set up logging for the monitor."""
        log_dir = Path.home() / 'Documents' / 'system-monitor-logs'
        log_dir.mkdir(exist_ok=True)
        
        # Clear any existing handlers to avoid file handle leaks
        logger = logging.getLogger(__name__)
        logger.handlers.clear()
        
        # Create file handler
        file_handler = logging.FileHandler(
            log_dir / f"monitor_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        
        self.logger = logger
    
    def get_system_info(self):
        """Collect current system information."""
        info = {
            'timestamp': datetime.now().isoformat(),
            'hostname': self.hostname,
            'system': self.system,
            'platform': platform.platform(),
            'uptime': self.get_uptime(),
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'disk': self.get_disk_info(),
            'network': self.get_network_info(),
            'processes': self.get_process_info(),
            'services': self.check_services(),
            'logs': self.analyze_logs()
        }
        
        # Check for temperature if available
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                info['temperature'] = self.get_temperature_info(temps)
        except (AttributeError, NotImplementedError):
            # Not all systems support temperature sensors
            pass
        
        return info
    
    def get_uptime(self) -> str:
        """Get system uptime."""
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        return f"{days}d {hours}h {minutes}m"
    
    def get_cpu_info(self):
        """Get CPU information."""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        return {
            'count': psutil.cpu_count(),
            'percent_avg': sum(cpu_percent) / len(cpu_percent),
            'percent_per_core': cpu_percent,
            'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            'load_average': os.getloadavg()
        }
    
    def get_memory_info(self):
        """Get memory information."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            'total_gb': round(mem.total / (1024**3), 2),
            'used_gb': round(mem.used / (1024**3), 2),
            'available_gb': round(mem.available / (1024**3), 2),
            'percent': mem.percent,
            'swap_total_gb': round(swap.total / (1024**3), 2),
            'swap_used_gb': round(swap.used / (1024**3), 2),
            'swap_percent': swap.percent
        }
    
    def get_disk_info(self):
        """Get disk usage information."""
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total_gb': round(usage.total / (1024**3), 2),
                    'used_gb': round(usage.used / (1024**3), 2),
                    'free_gb': round(usage.free / (1024**3), 2),
                    'percent': usage.percent
                })
            except PermissionError:
                continue
        return disks
    
    def get_network_info(self):
        """Get network information."""
        net_io = psutil.net_io_counters()
        connections = psutil.net_connections(kind='inet')
        
        return {
            'bytes_sent_gb': round(net_io.bytes_sent / (1024**3), 2),
            'bytes_recv_gb': round(net_io.bytes_recv / (1024**3), 2),
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'active_connections': len([c for c in connections if c.status == 'ESTABLISHED']),
            'listening_ports': len([c for c in connections if c.status == 'LISTEN'])
        }
    
    def get_process_info(self):
        """Get top processes by CPU and memory."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU and memory usage
        top_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]
        top_memory = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:5]
        
        return {
            'total': len(processes),
            'top_cpu': top_cpu,
            'top_memory': top_memory
        }
    
    def get_temperature_info(self, temps):
        """Get temperature information."""
        result = {}
        for name, entries in temps.items():
            result[name] = {
                'current': entries[0].current,
                'high': entries[0].high,
                'critical': entries[0].critical
            }
        return result
    
    def check_services(self):
        """Check status of configured services."""
        services = {}
        for service in self.config['monitoring']['check_services']:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                services[service] = result.stdout.strip() == 'active'
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                services[service] = None
        return services
    
    def analyze_logs(self):
        """Analyze system logs for issues."""
        log_analysis = {
            'errors': [],
            'warnings': [],
            'auth_failures': []
        }
        
        for log_file in self.config['monitoring']['log_files']:
            if not Path(log_file).exists():
                continue
            
            try:
                # Read last 1000 lines of log
                with subprocess.Popen(
                    ['tail', '-n', '1000', log_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                ) as proc:
                    lines = proc.stdout.readlines()
                    
                    for line in lines:
                        # Check for errors
                        if 'error' in line.lower() or 'failed' in line.lower():
                            log_analysis['errors'].append({
                                'file': log_file,
                                'line': line.strip()[:200]  # Truncate long lines
                            })
                        
                        # Check for warnings
                        elif 'warning' in line.lower() or 'warn' in line.lower():
                            log_analysis['warnings'].append({
                                'file': log_file,
                                'line': line.strip()[:200]
                            })
                        
                        # Check for authentication failures
                        elif 'authentication failure' in line.lower() or 'invalid user' in line.lower():
                            log_analysis['auth_failures'].append({
                                'file': log_file,
                                'line': line.strip()[:200]
                            })
            except Exception as e:
                self.logger.error(f"Error analyzing {log_file}: {e}")
        
        # Limit to last 10 of each type
        for key in log_analysis:
            log_analysis[key] = log_analysis[key][-10:]
        
        return log_analysis
    
    def check_alerts(self, info):
        """Check if any metrics exceed thresholds."""
        alerts = []
        
        # CPU alert
        if info['cpu']['percent_avg'] > self.thresholds['cpu_percent']:
            alerts.append(f"⚠️ High CPU usage: {info['cpu']['percent_avg']:.1f}%")
        
        # Memory alert
        if info['memory']['percent'] > self.thresholds['memory_percent']:
            alerts.append(f"⚠️ High memory usage: {info['memory']['percent']:.1f}%")
        
        # Disk alerts
        for disk in info['disk']:
            if disk['percent'] > self.thresholds['disk_percent']:
                alerts.append(f"⚠️ High disk usage on {disk['mountpoint']}: {disk['percent']:.1f}%")
        
        # Temperature alerts
        if 'temperature' in info:
            for sensor, temps in info['temperature'].items():
                if temps['current'] > self.thresholds['temp_celsius']:
                    alerts.append(f"⚠️ High temperature on {sensor}: {temps['current']}°C")
        
        # Service alerts
        for service, status in info['services'].items():
            if status is False:
                alerts.append(f"⚠️ Service {service} is not running")
        
        # Log alerts
        if len(info['logs']['errors']) > 5:
            alerts.append(f"⚠️ Multiple errors detected in system logs ({len(info['logs']['errors'])} errors)")
        
        if len(info['logs']['auth_failures']) > 0:
            alerts.append(f"⚠️ Authentication failures detected ({len(info['logs']['auth_failures'])} failures)")
        
        return alerts
    
    def generate_odf_report(self, info, alerts):
        """Generate LibreOffice-compatible ODF report."""
        # Create document
        doc = OpenDocumentText()
        
        # Add styles
        h1style = Style(name="Heading 1", family="paragraph")
        h1style.addElement(TextProperties(attributes={'fontsize': "24pt", 'fontweight': "bold"}))
        doc.styles.addElement(h1style)
        
        h2style = Style(name="Heading 2", family="paragraph")
        h2style.addElement(TextProperties(attributes={'fontsize': "18pt", 'fontweight': "bold"}))
        doc.styles.addElement(h2style)
        
        # Title
        doc.text.addElement(H(outlinelevel=1, stylename=h1style, text=f"System Health Report - {self.hostname}"))
        doc.text.addElement(P(text=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
        doc.text.addElement(P(text=f"System: {info['platform']}"))
        doc.text.addElement(P(text=f"Uptime: {info['uptime']}"))
        doc.text.addElement(P(text=""))
        
        # Alerts section
        if alerts:
            doc.text.addElement(H(outlinelevel=2, stylename=h2style, text="⚠️ Alerts"))
            alert_list = List()
            for alert in alerts:
                item = ListItem()
                item.addElement(P(text=alert))
                alert_list.addElement(item)
            doc.text.addElement(alert_list)
            doc.text.addElement(P(text=""))
        
        # CPU section
        doc.text.addElement(H(outlinelevel=2, stylename=h2style, text="CPU Information"))
        doc.text.addElement(P(text=f"CPU Cores: {info['cpu']['count']}"))
        doc.text.addElement(P(text=f"Average Usage: {info['cpu']['percent_avg']:.1f}%"))
        doc.text.addElement(P(text=f"Load Average: {', '.join(map(str, info['cpu']['load_average']))}"))
        doc.text.addElement(P(text=""))
        
        # Memory section
        doc.text.addElement(H(outlinelevel=2, stylename=h2style, text="Memory Information"))
        doc.text.addElement(P(text=f"Total: {info['memory']['total_gb']} GB"))
        doc.text.addElement(P(text=f"Used: {info['memory']['used_gb']} GB ({info['memory']['percent']:.1f}%)"))
        doc.text.addElement(P(text=f"Available: {info['memory']['available_gb']} GB"))
        doc.text.addElement(P(text=f"Swap Used: {info['memory']['swap_used_gb']} GB ({info['memory']['swap_percent']:.1f}%)"))
        doc.text.addElement(P(text=""))
        
        # Disk section
        doc.text.addElement(H(outlinelevel=2, stylename=h2style, text="Disk Usage"))
        for disk in info['disk']:
            doc.text.addElement(P(text=f"{disk['mountpoint']} ({disk['device']}):"))
            doc.text.addElement(P(text=f"  Used: {disk['used_gb']} GB / {disk['total_gb']} GB ({disk['percent']:.1f}%)"))
        doc.text.addElement(P(text=""))
        
        # Network section
        doc.text.addElement(H(outlinelevel=2, stylename=h2style, text="Network Statistics"))
        doc.text.addElement(P(text=f"Data Sent: {info['network']['bytes_sent_gb']} GB"))
        doc.text.addElement(P(text=f"Data Received: {info['network']['bytes_recv_gb']} GB"))
        doc.text.addElement(P(text=f"Active Connections: {info['network']['active_connections']}"))
        doc.text.addElement(P(text=f"Listening Ports: {info['network']['listening_ports']}"))
        doc.text.addElement(P(text=""))
        
        # Top processes section
        doc.text.addElement(H(outlinelevel=2, stylename=h2style, text="Top Processes"))
        doc.text.addElement(P(text="By CPU Usage:"))
        for proc in info['processes']['top_cpu']:
            doc.text.addElement(P(text=f"  {proc['name']}: {proc['cpu_percent']:.1f}%"))
        doc.text.addElement(P(text=""))
        doc.text.addElement(P(text="By Memory Usage:"))
        for proc in info['processes']['top_memory']:
            doc.text.addElement(P(text=f"  {proc['name']}: {proc['memory_percent']:.1f}%"))
        doc.text.addElement(P(text=""))
        
        # Services section
        doc.text.addElement(H(outlinelevel=2, stylename=h2style, text="Service Status"))
        for service, status in info['services'].items():
            status_text = "✓ Running" if status else "✗ Stopped" if status is False else "? Unknown"
            doc.text.addElement(P(text=f"{service}: {status_text}"))
        doc.text.addElement(P(text=""))
        
        # Log analysis section
        if any(info['logs'].values()):
            doc.text.addElement(H(outlinelevel=2, stylename=h2style, text="Recent Log Events"))
            
            if info['logs']['errors']:
                doc.text.addElement(P(text=f"Recent Errors ({len(info['logs']['errors'])}):"))
                for error in info['logs']['errors'][-3:]:  # Show last 3
                    doc.text.addElement(P(text=f"  {error['line'][:100]}..."))
            
            if info['logs']['auth_failures']:
                doc.text.addElement(P(text=f"Authentication Failures ({len(info['logs']['auth_failures'])}):"))
                for failure in info['logs']['auth_failures'][-3:]:
                    doc.text.addElement(P(text=f"  {failure['line'][:100]}..."))
        
        # Save document
        output_dir = Path(self.config['reports']['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.odt"
        filepath = output_dir / filename
        doc.save(filepath)
        
        self.logger.info(f"Report saved to {filepath}")
        return str(filepath)
    
    def send_email_thunderbird(self, subject: str, body: str, attachment: str = None):
        """Send email using Thunderbird's configured accounts."""
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = self.config['email']['from_email']
        msg['To'] = ', '.join(self.config['email']['to_emails'])
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachment if provided
        if attachment and Path(attachment).exists():
            with open(attachment, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {Path(attachment).name}'
                )
                msg.attach(part)
        
        # Try to send via local SMTP (Thunderbird needs to be configured)
        try:
            with smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port']) as server:
                if self.config['email']['use_authentication']:
                    # Note: Credentials should be stored securely, not in config
                    pass  # server.login(username, password)
                
                server.send_message(msg)
                self.logger.info(f"Email sent successfully to {self.config['email']['to_emails']}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            
            # Fallback: Open in Thunderbird for manual sending
            self.open_in_thunderbird(subject, body, attachment)
            return False
    
    def open_in_thunderbird(self, subject: str, body: str, attachment: str = None):
        """Open composed email in Thunderbird."""
        # Build Thunderbird command
        to_emails = ','.join(self.config['email']['to_emails'])
        
        # URL encode the subject and body
        import urllib.parse
        subject_encoded = urllib.parse.quote(subject)
        body_encoded = urllib.parse.quote(body)
        
        # Thunderbird compose URL
        mailto_url = f"mailto:{to_emails}?subject={subject_encoded}&body={body_encoded}"
        
        if attachment:
            # Note: Thunderbird doesn't support attachment via mailto, 
            # so we'll note it in the body
            body_with_note = f"{body}\n\nNote: Please attach the report file:\n{attachment}"
            body_encoded = urllib.parse.quote(body_with_note)
            mailto_url = f"mailto:{to_emails}?subject={subject_encoded}&body={body_encoded}"
        
        try:
            subprocess.run(['thunderbird', '-compose', mailto_url], check=False)
            self.logger.info("Email opened in Thunderbird for manual sending")
        except FileNotFoundError:
            self.logger.error("Thunderbird not found. Please install Thunderbird or configure SMTP.")
    
    def run_daily_report(self):
        """Run the daily system report."""
        self.logger.info("Starting daily system report generation")
        
        # Collect system information
        info = self.get_system_info()
        
        # Check for alerts
        alerts = self.check_alerts(info)
        
        # Generate ODF report
        report_path = self.generate_odf_report(info, alerts)
        
        # Prepare email
        if alerts:
            subject = f"⚠️ System Alert: {self.hostname} - {len(alerts)} issues detected"
            body = "System Health Alert!\n\n" + "\n".join(alerts)
        else:
            subject = f"✓ System Report: {self.hostname} - All systems normal"
            body = f"Daily system report for {self.hostname}.\n\nAll systems are operating normally.\n"
        
        body += f"\n\nDetailed report attached.\n\nGenerated: {datetime.now()}"
        
        # Send email
        self.send_email_thunderbird(subject, body, report_path)
        
        # Clean old reports
        self.clean_old_reports()
        
        self.logger.info("Daily report completed")
    
    def clean_old_reports(self):
        """Remove reports older than configured days."""
        output_dir = Path(self.config['reports']['output_dir'])
        if not output_dir.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.config['reports']['keep_days'])
        
        for report_file in output_dir.glob("system_report_*.odt"):
            if report_file.stat().st_mtime < cutoff_date.timestamp():
                report_file.unlink()
                self.logger.info(f"Deleted old report: {report_file.name}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="System Monitor and Report Generator")
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--test', action='store_true', help='Run a test report')
    parser.add_argument('--setup-cron', action='store_true', help='Setup daily cron job')
    
    args = parser.parse_args()
    
    monitor = SystemMonitor(args.config)
    
    if args.test:
        print("Running test report...")
        monitor.run_daily_report()
        print(f"Report saved to: {monitor.config['reports']['output_dir']}")
    
    elif args.setup_cron:
        # Add cron job for daily reports
        cron_command = f"0 8 * * * /usr/bin/python3 {Path(__file__).absolute()} --config {args.config or 'default'}"
        
        print("Add this line to your crontab (crontab -e):")
        print(cron_command)
        print("\nThis will run the system monitor daily at 8:00 AM")
    
    else:
        monitor.run_daily_report()


if __name__ == "__main__":
    main()