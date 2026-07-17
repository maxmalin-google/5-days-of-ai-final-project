from typing import List, Dict
import asyncio
from observability import get_tracer, log_event

tracer = get_tracer(__name__)

class MockVectorStore:
    def __init__(self):
        # Simulated database of company policies
        self.documents = [
            "SOC2-001: All Google Cloud Storage buckets must not have allUsers or allAuthenticatedUsers in their IAM bindings. Public access is strictly forbidden.",
            "SOC2-002: All IAM roles should enforce least privilege. Avoid using roles/editor or roles/owner.",
            "SOC2-003: Cloud SQL instances must have authorized networks configured and require SSL."
        ]
        
    def similarity_search(self, query: str) -> List[str]:
        """
        Simulates a vector database similarity search.
        """
        with tracer.start_as_current_span("vector_db_search"):
            log_event("INTENT", "Querying Vector DB", {"query": query})
            
            # Simple keyword matching to mock semantic search
            results = []
            for doc in self.documents:
                if any(word in doc.lower() for word in query.lower().split()):
                    results.append(doc)
                    
            if not results:
                # Fallback to generic policy if no match
                results = ["General Policy: Ensure all resources follow least privilege and deny public access."]
                
            log_event("OUTCOME", "Vector DB Search complete", {"results_count": len(results)})
            return results

# Singleton instance
vector_store = MockVectorStore()

def query_security_policy(query: str) -> dict:
    """Tool function to query the internal security policy database."""
    docs = vector_store.similarity_search(query)
    return {"status": "success", "policies": docs}


class ContextCompactor:
    """
    Implements history compaction to manage context bloat across long agent sessions.
    """
    def __init__(self, max_history: int = 10):
        self.history: List[Dict] = []
        self.max_history = max_history
        
    def add_interaction(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        # Schedule compaction as an async background task to prevent UI blocking
        asyncio.create_task(self.compact())
        
    async def compact(self):
        """
        If history exceeds limits, summarize the older messages asynchronously.
        """
        if len(self.history) > self.max_history:
            log_event("SYS", "Async Compaction Started", {"current_size": len(self.history)})
            
            # Mocking an expensive LLM call to summarize history
            await asyncio.sleep(1) 
            
            # Keep system prompt (index 0) and the most recent N-1 messages
            system_prompt = self.history[0]
            recent_messages = self.history[-(self.max_history - 1):]
            self.history = [system_prompt] + recent_messages
            
            log_event("SYS", "Async Compaction Completed", {"new_size": len(self.history)})
