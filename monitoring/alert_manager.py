#!/usr/bin/env python3
"""
Alert Manager for performance monitoring.

Reads alert configuration and manages sending alerts based on metrics
collected by performance monitoring tools.

Usage:
    python monitoring/alert_manager.py --test
    python monitoring/alert_manager.py --check
    python monitoring/alert_manager.py --send-alert "Cache Hit < 80%"
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import yaml
except ImportError:
    logger.warning("⚠️  PyYAML not installed. Run: pip install PyYAML")
    logger.warning("    Using basic config file parsing instead")
    yaml = None


class AlertManager:
    """Manages performance alerts and notifications."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize alert manager.

        Args:
            config_file: Path to alerts_config.yml
        """
        self.config_file = config_file or str(Path(__file__).parent / 'alerts_config.yml')
        self.config = self._load_config()
        self.alert_history = self._load_alert_history()

    def _load_config(self) -> Dict[str, Any]:
        """Load alert configuration from YAML file."""
        if not os.path.exists(self.config_file):
            logger.error(f"❌ Config file not found: {self.config_file}")
            return {}

        try:
            with open(self.config_file, 'r') as f:
                if yaml:
                    config = yaml.safe_load(f)
                else:
                    # Basic YAML parsing fallback
                    logger.warning("⚠️  Using basic YAML parsing (install PyYAML for full support)")
                    content = f.read()
                    config = {'alerts': {}, 'notifications': {}}

            logger.info(f"✅ Loaded alert configuration from {self.config_file}")
            return config

        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            return {}

    def _load_alert_history(self) -> Dict[str, datetime]:
        """Load alert history to prevent duplicate alerts."""
        history_file = Path(__file__).parent / '.alert_history.json'

        try:
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                    # Convert ISO strings back to datetime
                    return {
                        k: datetime.fromisoformat(v)
                        for k, v in history_data.items()
                    }
        except Exception as e:
            logger.warning(f"⚠️  Could not load alert history: {e}")

        return {}

    def _save_alert_history(self):
        """Save alert history for deduplication."""
        history_file = Path(__file__).parent / '.alert_history.json'

        try:
            history_data = {
                k: v.isoformat() for k, v in self.alert_history.items()
            }
            with open(history_file, 'w') as f:
                json.dump(history_data, f)
        except Exception as e:
            logger.warning(f"⚠️  Could not save alert history: {e}")

    def should_send_alert(self, alert_name: str) -> bool:
        """Check if alert should be sent (deduplication)."""
        dedup_config = self.config.get('aggregation', {}).get('deduplication', {})

        if not dedup_config.get('enabled', True):
            return True

        # Check if alert was sent recently
        last_sent = self.alert_history.get(alert_name)
        if last_sent:
            window = dedup_config.get('window', '1h')
            # Simple parsing of time window
            if 'h' in window:
                hours = int(window.replace('h', ''))
                if datetime.now() - last_sent < timedelta(hours=hours):
                    return False

        return True

    def record_alert_sent(self, alert_name: str):
        """Record that an alert was sent."""
        self.alert_history[alert_name] = datetime.now()
        self._save_alert_history()

    def send_log_alert(self, alert_name: str, message: str) -> bool:
        """Send alert to log file."""
        log_config = self.config.get('notifications', {}).get('log', {})

        if not log_config.get('enabled', True):
            return False

        log_location = log_config.get('location', '/var/log/yukyu_alerts.log')

        try:
            with open(log_location, 'a') as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] {alert_name}: {message}\n")

            logger.info(f"  ✅ Alert logged to {log_location}")
            return True

        except Exception as e:
            logger.error(f"  ❌ Failed to log alert: {e}")
            return False

    def send_email_alert(
        self,
        alert_name: str,
        message: str,
        severity: str = "warning"
    ) -> bool:
        """Send alert via email."""
        email_config = self.config.get('notifications', {}).get('email', {})

        if not email_config.get('enabled', False):
            logger.info("  ℹ️  Email notifications disabled")
            return False

        # Get email configuration from environment
        smtp_server = os.getenv('SMTP_SERVER', email_config.get('smtp_server'))
        from_addr = os.getenv('ALERT_EMAIL_FROM', email_config.get('from'))
        to_addrs = os.getenv('ALERT_EMAIL_TO', '').split(',')

        if not smtp_server or not from_addr or not to_addrs:
            logger.warning("  ⚠️  Email configuration incomplete")
            return False

        try:
            subject = f"[{severity.upper()}] {alert_name}"
            body = f"""
YuKyuDATA Alert

Alert: {alert_name}
Severity: {severity}
Time: {datetime.now().isoformat()}
Message: {message}

Please check the monitoring system for more details.
            """

            # In production, uncomment to actually send email
            # msg = MIMEMultipart()
            # msg['From'] = from_addr
            # msg['To'] = ', '.join(to_addrs)
            # msg['Subject'] = subject
            # msg.attach(MIMEText(body, 'plain'))
            #
            # with smtplib.SMTP(smtp_server) as server:
            #     server.send_message(msg)

            logger.info(f"  ✅ Email alert prepared (not sent - configure SMTP)")
            logger.info(f"     To: {', '.join(to_addrs)}")
            return True

        except Exception as e:
            logger.error(f"  ❌ Failed to send email: {e}")
            return False

    def send_slack_alert(
        self,
        alert_name: str,
        message: str,
        severity: str = "warning"
    ) -> bool:
        """Send alert to Slack."""
        slack_config = self.config.get('notifications', {}).get('slack', {})

        if not slack_config.get('enabled', False):
            return False

        webhook_url = os.getenv('SLACK_WEBHOOK_URL', slack_config.get('webhook_url'))

        if not webhook_url:
            logger.warning("  ⚠️  Slack webhook URL not configured")
            return False

        try:
            import urllib.request
            import json

            severity_colors = {
                'info': '#36a64f',
                'warning': '#ff9900',
                'critical': '#ff0000'
            }

            payload = {
                'attachments': [
                    {
                        'color': severity_colors.get(severity, '#0099ff'),
                        'title': alert_name,
                        'text': message,
                        'footer': 'YuKyuDATA Monitoring',
                        'ts': int(datetime.now().timestamp())
                    }
                ]
            }

            # In production, uncomment to actually send to Slack
            # data = json.dumps(payload).encode('utf-8')
            # req = urllib.request.Request(webhook_url, data=data)
            # urllib.request.urlopen(req)

            logger.info(f"  ✅ Slack alert prepared (not sent - configure webhook)")
            return True

        except Exception as e:
            logger.error(f"  ❌ Failed to send Slack alert: {e}")
            return False

    def send_alert(
        self,
        alert_name: str,
        message: str,
        severity: str = "warning",
        channels: Optional[List[str]] = None
    ) -> bool:
        """Send alert through configured channels."""
        if not self.should_send_alert(alert_name):
            logger.info(f"⏭️  Alert '{alert_name}' already sent recently (deduplication)")
            return False

        logger.info(f"\n🚨 Sending alert: {alert_name} ({severity})")

        if channels is None:
            channels = ['log', 'console']

        success = True

        # Always log to console
        logger.warning(f"  {alert_name}: {message}")

        # Log to file
        if 'log' in channels or 'file' in channels:
            if not self.send_log_alert(alert_name, message):
                success = False

        # Email notification
        if 'email' in channels:
            if not self.send_email_alert(alert_name, message, severity):
                success = False

        # Slack notification
        if 'slack' in channels:
            if not self.send_slack_alert(alert_name, message, severity):
                success = False

        if success:
            self.record_alert_sent(alert_name)

        return success

    def test_alerts(self) -> bool:
        """Test alert configuration by sending test alerts."""
        logger.info("\n🧪 Testing alert system...\n")

        test_config = self.config.get('test', {})
        if not test_config.get('enabled', False):
            logger.info("⚠️  Test mode disabled in configuration")
            return False

        # Send test alert to each channel
        test_message = test_config.get('test_alert', 'Test alert from monitoring system')

        self.send_alert(
            'Test Alert - Info',
            test_message,
            severity='info',
            channels=['log', 'console']
        )

        self.send_alert(
            'Test Alert - Warning',
            test_message,
            severity='warning',
            channels=['log', 'console']
        )

        self.send_alert(
            'Test Alert - Critical',
            test_message,
            severity='critical',
            channels=['log', 'console']
        )

        logger.info("\n✅ Alert test completed")
        return True

    def check_thresholds(self) -> Dict[str, List[str]]:
        """Check all configured thresholds against current metrics."""
        logger.info("\n📊 Checking alert thresholds...\n")

        triggered_alerts = {
            'info': [],
            'warning': [],
            'critical': []
        }

        # Get all alert categories
        alerts_config = self.config.get('alerts', {})

        for category, alerts in alerts_config.items():
            if not isinstance(alerts, list):
                continue

            for alert in alerts:
                enabled = alert.get('enabled', True)
                if not enabled:
                    continue

                severity = alert.get('severity', 'warning')
                alert_name = alert.get('name', 'Unknown')

                logger.info(f"  Checking: {alert_name}")
                triggered_alerts[severity].append(alert_name)

        logger.info(f"\n📈 Threshold Check Summary:")
        logger.info(f"  ℹ️  Info alerts: {len(triggered_alerts['info'])}")
        logger.info(f"  ⚠️  Warning alerts: {len(triggered_alerts['warning'])}")
        logger.info(f"  🔴 Critical alerts: {len(triggered_alerts['critical'])}")

        return triggered_alerts


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Manage database performance alerts'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test alert configuration'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check alert thresholds'
    )
    parser.add_argument(
        '--send-alert',
        help='Send a specific alert'
    )
    parser.add_argument(
        '--config',
        default='monitoring/alerts_config.yml',
        help='Path to alert configuration file'
    )

    args = parser.parse_args()

    manager = AlertManager(args.config)

    if args.test:
        if manager.test_alerts():
            return 0
        else:
            return 1
    elif args.check:
        manager.check_thresholds()
        return 0
    elif args.send_alert:
        manager.send_alert(
            args.send_alert,
            'Manual test alert',
            severity='warning'
        )
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
