from typing import List, Dict
import asyncio
import chromadb
from observability import get_tracer, log_event

tracer = get_tracer(__name__)

class ChromaVectorStore:
    """
    Connects to a persistent local Vector Store (ChromaDB) to retrieve information.
    Fulfills the persistent database requirement without needing cloud credentials.
    """
    def __init__(self, db_path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Get or create the collection for security policies
        self.collection = self.client.get_or_create_collection(name="security_policies")
        
        # Initialize mock policies if empty
        if self.collection.count() == 0:
            self._seed_database()

    def _seed_database(self):
        log_event("SYS", "Seeding ChromaDB with initial security policies.", {})
        policies = [
            "SOC2-001: All Google Cloud Storage buckets must not have allUsers or allAuthenticatedUsers in their IAM bindings. Public access is strictly forbidden.",
            "SOC2-002: All IAM roles should enforce least privilege. Avoid using roles/editor or roles/owner.",
            "SOC2-003: Cloud SQL instances must have authorized networks configured and require SSL."
        ]
        self.collection.add(
            documents=policies,
            metadatas=[{"source": "soc2"} for _ in policies],
            ids=[f"policy_{i}" for i in range(len(policies))]
        )
        
    def similarity_search(self, query: str) -> List[str]:
        """
        Queries the persistent ChromaDB vector store.
        """
        with tracer.start_as_current_span("vector_db_search"):
            log_event("INTENT", "Querying Vector DB", {"query": query})
            
            results = self.collection.query(
                query_texts=[query],
                n_results=1
            )
            
            docs = results['documents'][0] if results['documents'] else []
            if not docs:
                docs = ["General Policy: Ensure all resources follow least privilege and deny public access."]
                
            log_event("OUTCOME", "Vector DB Search complete", {"results_count": len(docs)})
            return docs

# Singleton instance
vector_store = ChromaVectorStore()

def query_security_policy(query: str) -> dict:
    """Tool function to query the persistent security policy database."""
    docs = vector_store.similarity_search(query)
    return {"status": "success", "policies": docs}


class ContextCompactor:
    """
    Implements history compaction to manage context bloat across long agent sessions.
    Stores history in ChromaDB as well for persistent sessions.
    """
    def __init__(self, max_history: int = 10, db_path: str = "./chroma_db"):
        self.history: List[Dict] = []
        self.max_history = max_history
        self.client = chromadb.PersistentClient(path=db_path)
        self.history_collection = self.client.get_or_create_collection(name="session_history")
        
    def add_interaction(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        
        # Persist to local vector store
        self.history_collection.add(
            documents=[content],
            metadatas=[{"role": role}],
            ids=[f"msg_{len(self.history)}"]
        )
        
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
