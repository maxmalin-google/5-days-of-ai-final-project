import json
import logging
import re
from datetime import datetime
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# Setup OpenTelemetry Tracer
trace.set_tracer_provider(TracerProvider())
tracer_provider = trace.get_tracer_provider()
tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

def get_tracer(module_name: str):
    return trace.get_tracer(module_name)

class PIIRedactionFormatter(logging.Formatter):
    """
    Custom JSON Formatter that scrubs PII (Emails, IP Addresses).
    In this implementation, it simulates a call to the Google Cloud DLP API.
    """
    EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    IP_REGEX = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    
    def _call_cloud_dlp_mock(self, text: str) -> str:
        """Simulates sending the payload to Google Cloud DLP for inspection and de-identification."""
        text = re.sub(self.EMAIL_REGEX, "[REDACTED_BY_CLOUD_DLP]", text)
        text = re.sub(self.IP_REGEX, "[REDACTED_BY_CLOUD_DLP]", text)
        return text
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        
        # Add structured context if available
        if hasattr(record, "intent"):
            log_data["intent"] = record.intent
        if hasattr(record, "metadata"):
            log_data["metadata"] = record.metadata
            
        json_log = json.dumps(log_data)
        
        # Redact PII using the mock Google Cloud DLP API
        json_log = self._call_cloud_dlp_mock(json_log)
        
        return json_log

# Setup logger
logger = logging.getLogger("DevSecOpsAgent")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(PIIRedactionFormatter())
logger.addHandler(handler)

def log_event(event_type: str, message: str, metadata: dict = None):
    """
    Helper function to log intent vs outcome structurally.
    event_type should be 'INTENT', 'OUTCOME', or 'SYS'
    """
    extra = {"intent": event_type, "metadata": metadata or {}}
    logger.info(message, extra=extra)
