import boto3
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
import streamlit as st


class AWSQueueMonitor:
    """Monitor AWS SQS queues in a separate thread"""

    def __init__(self, region_name: str = 'eu-west-1', queue_names: Optional[List[str]] = None):
        """
        Initialize AWS Queue Monitor

        Args:
            region_name: AWS region name (default: eu-west-1)
            queue_names: List of queue names to monitor. If None, monitors all queues.
        """
        self.region_name = region_name
        self.queue_names = queue_names or []
        self.sqs_client = None
        self.monitoring = False
        self.monitor_thread = None
        self.queue_data = {}
        self.last_update = None
        self.update_interval = 30  # seconds
        self.error_message = None

    def initialize_client(self, aws_access_key_id: Optional[str] = None,
                         aws_secret_access_key: Optional[str] = None,
                         profile_name: Optional[str] = None,
                         aws_session_token: Optional[str] = None):
        """
        Initialize SQS client with credentials

        Args:
            aws_access_key_id: AWS access key (optional if using profile or env vars)
            aws_secret_access_key: AWS secret key (optional if using profile or env vars)
            profile_name: AWS profile name (optional)
            aws_session_token: AWS session token for temporary credentials (optional)
        """
        try:
            if profile_name:
                session = boto3.Session(profile_name=profile_name)
                self.sqs_client = session.client('sqs', region_name=self.region_name)
            elif aws_access_key_id and aws_secret_access_key:
                client_kwargs = {
                    'service_name': 'sqs',
                    'region_name': self.region_name,
                    'aws_access_key_id': aws_access_key_id,
                    'aws_secret_access_key': aws_secret_access_key
                }
                # Add session token if provided (for temporary credentials)
                if aws_session_token:
                    client_kwargs['aws_session_token'] = aws_session_token

                self.sqs_client = boto3.client(**client_kwargs)
            else:
                # Use default credentials (env vars or IAM role)
                self.sqs_client = boto3.client('sqs', region_name=self.region_name)

            self.error_message = None
            return True
        except Exception as e:
            self.error_message = f"Erro ao inicializar cliente AWS: {str(e)}"
            return False

    def get_queue_urls(self) -> List[Dict[str, str]]:
        """Get URLs for specified queues or all queues"""
        try:
            if not self.sqs_client:
                return []

            if self.queue_names:
                # Get specific queues
                queue_urls = []
                for queue_name in self.queue_names:
                    try:
                        response = self.sqs_client.get_queue_url(QueueName=queue_name)
                        queue_urls.append({
                            'name': queue_name,
                            'url': response['QueueUrl']
                        })
                    except self.sqs_client.exceptions.QueueDoesNotExist:
                        self.error_message = f"Fila '{queue_name}' não encontrada"
                return queue_urls
            else:
                # List all queues
                response = self.sqs_client.list_queues()
                queue_urls = []
                if 'QueueUrls' in response:
                    for url in response['QueueUrls']:
                        queue_name = url.split('/')[-1]
                        queue_urls.append({
                            'name': queue_name,
                            'url': url
                        })
                return queue_urls
        except Exception as e:
            self.error_message = f"Erro ao listar filas: {str(e)}"
            return []

    def get_queue_attributes(self, queue_url: str) -> Dict:
        """Get attributes for a specific queue"""
        try:
            response = self.sqs_client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=[
                    'ApproximateNumberOfMessages',
                    'ApproximateNumberOfMessagesNotVisible',
                    'ApproximateNumberOfMessagesDelayed',
                    'CreatedTimestamp',
                    'LastModifiedTimestamp'
                ]
            )
            return response.get('Attributes', {})
        except Exception as e:
            self.error_message = f"Erro ao obter atributos da fila: {str(e)}"
            return {}

    def fetch_queue_data(self):
        """Fetch data for all queues"""
        queue_urls = self.get_queue_urls()

        for queue_info in queue_urls:
            queue_name = queue_info['name']
            queue_url = queue_info['url']
            attributes = self.get_queue_attributes(queue_url)

            self.queue_data[queue_name] = {
                'messages_available': int(attributes.get('ApproximateNumberOfMessages', 0)),
                'messages_in_flight': int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0)),
                'messages_delayed': int(attributes.get('ApproximateNumberOfMessagesDelayed', 0)),
                'total_messages': (
                    int(attributes.get('ApproximateNumberOfMessages', 0)) +
                    int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0)) +
                    int(attributes.get('ApproximateNumberOfMessagesDelayed', 0))
                ),
                'created_timestamp': attributes.get('CreatedTimestamp', ''),
                'last_modified': attributes.get('LastModifiedTimestamp', ''),
                'url': queue_url
            }

        self.last_update = datetime.now()

    def monitor_loop(self):
        """Main monitoring loop running in separate thread"""
        while self.monitoring:
            try:
                self.fetch_queue_data()
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

    def get_queue_data(self) -> Dict:
        """Get current queue data"""
        return self.queue_data.copy()

    def get_last_update(self) -> Optional[datetime]:
        """Get timestamp of last update"""
        return self.last_update

    def set_update_interval(self, seconds: int):
        """Set update interval in seconds"""
        self.update_interval = max(10, seconds)  # Minimum 10 seconds

    def get_error_message(self) -> Optional[str]:
        """Get last error message"""
        return self.error_message

    def clear_error(self):
        """Clear error message"""
        self.error_message = None


# Singleton instance for the app
_monitor_instance = None


def get_monitor_instance() -> AWSQueueMonitor:
    """Get or create the global monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = AWSQueueMonitor()
    return _monitor_instance
