import boto3
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
import streamlit as st


class DynamoDBMonitor:
    """Monitor DynamoDB table for expiring items"""

    def __init__(self, region_name: str = 'eu-west-1', table_name: str = 'dcxstg-dev-converter-work-pool'):
        """
        Initialize DynamoDB Monitor

        Args:
            region_name: AWS region name (default: eu-west-1)
            table_name: DynamoDB table name
        """
        self.region_name = region_name
        self.table_name = table_name
        self.dynamodb_client = None
        self.monitoring = False
        self.monitor_thread = None
        self.table_data = []
        self.last_update = None
        self.update_interval = 5  # seconds (mais frequente para expiração)
        self.error_message = None

    def initialize_client(self, aws_access_key_id: Optional[str] = None,
                         aws_secret_access_key: Optional[str] = None,
                         profile_name: Optional[str] = None,
                         aws_session_token: Optional[str] = None):
        """
        Initialize DynamoDB client with credentials

        Args:
            aws_access_key_id: AWS access key (optional if using profile or env vars)
            aws_secret_access_key: AWS secret key (optional if using profile or env vars)
            profile_name: AWS profile name (optional)
            aws_session_token: AWS session token for temporary credentials (optional)
        """
        try:
            if profile_name:
                session = boto3.Session(profile_name=profile_name)
                self.dynamodb_client = session.client('dynamodb', region_name=self.region_name)
            elif aws_access_key_id and aws_secret_access_key:
                client_kwargs = {
                    'service_name': 'dynamodb',
                    'region_name': self.region_name,
                    'aws_access_key_id': aws_access_key_id,
                    'aws_secret_access_key': aws_secret_access_key
                }
                # Add session token if provided (for temporary credentials)
                if aws_session_token:
                    client_kwargs['aws_session_token'] = aws_session_token

                self.dynamodb_client = boto3.client(**client_kwargs)
            else:
                # Use default credentials (env vars or IAM role)
                self.dynamodb_client = boto3.client('dynamodb', region_name=self.region_name)

            self.error_message = None
            return True
        except Exception as e:
            self.error_message = f"Erro ao inicializar cliente AWS: {str(e)}"
            return False

    def fetch_table_data(self):
        """Fetch data from DynamoDB table"""
        try:
            if not self.dynamodb_client:
                return

            # Scan table
            response = self.dynamodb_client.scan(
                TableName=self.table_name,
                ProjectionExpression='entity_name, expires, uid'
            )

            items = response.get('Items', [])

            # Parse items
            self.table_data = []
            current_time = int(datetime.now(timezone.utc).timestamp())

            for item in items:
                entity_name = item.get('entity_name', {}).get('S', 'N/A')
                expires_timestamp = int(item.get('expires', {}).get('N', 0))
                uid = item.get('uid', {}).get('S', 'N/A')

                # Calculate time difference
                time_diff = expires_timestamp - current_time

                # Determine status
                if time_diff > 0:
                    status = 'active'  # Verde: ainda não expirou
                elif time_diff >= -10:
                    status = 'warning'  # Amarelo: expirado até 10 segundos
                else:
                    status = 'expired'  # Vermelho: expirado há mais de 10 segundos

                self.table_data.append({
                    'entity_name': entity_name,
                    'uid': uid,
                    'expires': expires_timestamp,
                    'expires_formatted': datetime.fromtimestamp(expires_timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                    'time_diff': time_diff,
                    'status': status
                })

            # Sort by expires timestamp (closest to expiring first)
            self.table_data.sort(key=lambda x: x['expires'])

            self.last_update = datetime.now()

        except Exception as e:
            self.error_message = f"Erro ao buscar dados do DynamoDB: {str(e)}"

    def monitor_loop(self):
        """Main monitoring loop running in separate thread"""
        while self.monitoring:
            try:
                self.fetch_table_data()
                time.sleep(self.update_interval)
            except Exception as e:
                self.error_message = f"Erro no loop de monitoramento: {str(e)}"
                time.sleep(self.update_interval)

    def start_monitoring(self):
        """Start monitoring in a separate thread"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

    def get_table_data(self) -> List[Dict]:
        """Get current table data"""
        return self.table_data.copy()

    def get_last_update(self) -> Optional[datetime]:
        """Get timestamp of last update"""
        return self.last_update

    def set_update_interval(self, seconds: int):
        """Set update interval in seconds"""
        self.update_interval = max(5, seconds)  # Minimum 5 seconds

    def get_error_message(self) -> Optional[str]:
        """Get last error message"""
        return self.error_message

    def clear_error(self):
        """Clear error message"""
        self.error_message = None


# Singleton instance for the app
_dynamodb_monitor_instance = None


def get_dynamodb_monitor_instance() -> DynamoDBMonitor:
    """Get or create the global monitor instance"""
    global _dynamodb_monitor_instance
    if _dynamodb_monitor_instance is None:
        _dynamodb_monitor_instance = DynamoDBMonitor()
    return _dynamodb_monitor_instance
