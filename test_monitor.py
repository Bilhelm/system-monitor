#!/usr/bin/env python3
"""
Tests for System Monitor
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from system_monitor import SystemMonitor


class TestSystemMonitor(unittest.TestCase):
    """Test cases for System Monitor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'email': {
                'smtp_server': 'localhost',
                'smtp_port': 25,
                'from_email': 'test@localhost',
                'to_emails': ['admin@localhost'],
                'use_authentication': False
            },
            'reports': {
                'output_dir': self.temp_dir,
                'keep_days': 30
            },
            'monitoring': {
                'check_services': ['ssh'],
                'log_files': []
            }
        }
        
        # Save config to temp file
        self.config_file = Path(self.temp_dir) / 'config.json'
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)
        
        self.monitor = SystemMonitor(str(self.config_file))
    
    def test_system_info_collection(self):
        """Test that system info is collected properly."""
        info = self.monitor.get_system_info()
        
        # Check required keys
        self.assertIn('timestamp', info)
        self.assertIn('hostname', info)
        self.assertIn('cpu', info)
        self.assertIn('memory', info)
        self.assertIn('disk', info)
        self.assertIn('network', info)
        self.assertIn('processes', info)
        
        # Check CPU info
        self.assertIn('count', info['cpu'])
        self.assertIn('percent_avg', info['cpu'])
        self.assertIsInstance(info['cpu']['count'], int)
        self.assertGreater(info['cpu']['count'], 0)
        
        # Check memory info
        self.assertIn('total_gb', info['memory'])
        self.assertIn('percent', info['memory'])
        self.assertGreater(info['memory']['total_gb'], 0)
        
        # Check disk info
        self.assertIsInstance(info['disk'], list)
        if info['disk']:
            self.assertIn('mountpoint', info['disk'][0])
            self.assertIn('percent', info['disk'][0])
    
    def test_alert_detection(self):
        """Test alert detection with threshold crossing."""
        # Create mock info with high values
        mock_info = {
            'cpu': {'percent_avg': 85},  # Above threshold
            'memory': {'percent': 90},   # Above threshold
            'disk': [
                {'mountpoint': '/', 'percent': 95}  # Above threshold
            ],
            'services': {'ssh': False},  # Service down
            'logs': {
                'errors': [{'line': 'error'}] * 10,  # Many errors
                'warnings': [],
                'auth_failures': [{'line': 'auth fail'}]
            }
        }
        
        alerts = self.monitor.check_alerts(mock_info)
        
        # Should have multiple alerts
        self.assertGreater(len(alerts), 0)
        
        # Check specific alerts
        self.assertTrue(any('CPU' in alert for alert in alerts))
        self.assertTrue(any('memory' in alert for alert in alerts))
        self.assertTrue(any('disk' in alert for alert in alerts))
        self.assertTrue(any('ssh' in alert for alert in alerts))
    
    def test_odf_report_generation(self):
        """Test ODF report generation."""
        info = self.monitor.get_system_info()
        alerts = []
        
        report_path = self.monitor.generate_odf_report(info, alerts)
        
        # Check report was created
        self.assertTrue(Path(report_path).exists())
        self.assertTrue(report_path.endswith('.odt'))
        
        # Check file size (should have content)
        self.assertGreater(Path(report_path).stat().st_size, 1000)
    
    def test_uptime_format(self):
        """Test uptime formatting."""
        uptime = self.monitor.get_uptime()
        
        # Should be in format "Xd Xh Xm"
        self.assertRegex(uptime, r'\d+d \d+h \d+m')
    
    def test_config_loading(self):
        """Test configuration loading."""
        # Test with existing config
        monitor = SystemMonitor(str(self.config_file))
        self.assertEqual(monitor.config['email']['from_email'], 'test@localhost')
        
        # Test with non-existent config (should use defaults)
        monitor2 = SystemMonitor('nonexistent.json')
        self.assertIn('email', monitor2.config)
        self.assertIn('reports', monitor2.config)
    
    @patch('subprocess.run')
    def test_service_checking(self, mock_run):
        """Test service status checking."""
        # Mock systemctl response
        mock_run.return_value = MagicMock(stdout='active\n')
        
        services = self.monitor.check_services()
        
        # Should have called systemctl
        mock_run.assert_called()
        
        # Should return service status
        self.assertIn('ssh', services)
    
    def test_process_info(self):
        """Test process information gathering."""
        proc_info = self.monitor.get_process_info()
        
        self.assertIn('total', proc_info)
        self.assertIn('top_cpu', proc_info)
        self.assertIn('top_memory', proc_info)
        
        # Should have some processes
        self.assertGreater(proc_info['total'], 0)
        
        # Top lists should be limited to 5
        self.assertLessEqual(len(proc_info['top_cpu']), 5)
        self.assertLessEqual(len(proc_info['top_memory']), 5)
    
    @patch('smtplib.SMTP')
    def test_email_sending(self, mock_smtp):
        """Test email sending functionality."""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = self.monitor.send_email_thunderbird(
            "Test Subject",
            "Test Body",
            None
        )
        
        # Should have tried to send
        mock_server.send_message.assert_called_once()
    
    def test_network_info(self):
        """Test network information gathering."""
        net_info = self.monitor.get_network_info()
        
        self.assertIn('bytes_sent_gb', net_info)
        self.assertIn('bytes_recv_gb', net_info)
        self.assertIn('active_connections', net_info)
        self.assertIn('listening_ports', net_info)
        
        # Values should be non-negative
        self.assertGreaterEqual(net_info['bytes_sent_gb'], 0)
        self.assertGreaterEqual(net_info['bytes_recv_gb'], 0)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)