from observability import get_tracer, log_event

tracer = get_tracer(__name__)

class SecretManager:
    """
    Mocks Google Cloud Secret Manager to securely inject secrets 
    into the application at runtime without hardcoding them.
    """
    def __init__(self, project_id: str = "my-gcp-project"):
        self.project_id = project_id
        
        # In a real environment, this would not exist in the code.
        # This dictionary simulates the remote Secret Manager backend.
        self._mock_backend = {
            "projects/my-gcp-project/secrets/llm-api-key/versions/latest": "AIzaSyMockKey_1234567890",
            "projects/my-gcp-project/secrets/vector-db-token/versions/latest": "pinecone-mock-token-xyz"
        }

    def access_secret_version(self, secret_id: str, version_id: str = "latest") -> str:
        """
        Retrieves a secret payload.
        """
        with tracer.start_as_current_span("access_secret_manager"):
            secret_name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version_id}"
            log_event("SYS", "Fetching secret securely", {"secret_name": secret_name})
            
            payload = self._mock_backend.get(secret_name)
            if not payload:
                raise ValueError(f"Secret {secret_name} not found in Secret Manager.")
                
            return payload

# Singleton instance for the application to use
secret_manager = SecretManager()
