"""
Quantum Vector Service using Qdrant for knowledge base search
"""
from app.core.config import (
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    QDRANT_TIMEOUT_SEC,
    EMBEDDING_MODEL,
    VECTOR_SIZE,
    TOP_K,
    RETRIEVAL_MIN_SCORE
)

# Optional imports
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("[WARN] SentenceTransformers not available")

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import (
        Distance, VectorParams, PointStruct, Filter, 
        FieldCondition, MatchValue, PayloadSchemaType
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("[WARN] Qdrant client not available")


class QuantumVectorService:
    """Quantum-inspired vector database service using Qdrant"""
    
    def __init__(self):
        self.client = None
        self.embedding_model = None
        self.initialize_services()
    
    def initialize_services(self):
        """Initialize Qdrant client and embedding model"""
        if QDRANT_AVAILABLE:
            try:
                self.client = QdrantClient(
                    url=QDRANT_URL,
                    api_key=QDRANT_API_KEY,
                    timeout=QDRANT_TIMEOUT_SEC,
                )
                print("[OK] Qdrant client initialized successfully")
            except Exception as e:
                print(f"[ERROR] Qdrant client initialization failed: {e}")
                self.client = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
                print("[OK] Embedding model initialized successfully")
            except Exception as e:
                print(f"[ERROR] Embedding model initialization failed: {e}")
                self.embedding_model = None
    
    def ensure_collection(self):
        """Ensure Qdrant collection exists with proper configuration"""
        if not self.client:
            return False
        
        try:
            collections = self.client.get_collections().collections
            names = {c.name for c in collections}
            
            if QDRANT_COLLECTION not in names:
                self.client.create_collection(
                    collection_name=QDRANT_COLLECTION,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                )
                print(f"[OK] Created Qdrant collection: {QDRANT_COLLECTION}")
            
            # Ensure payload indexes
            try:
                self.client.create_payload_index(
                    collection_name=QDRANT_COLLECTION,
                    field_name="trimester",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            except Exception:
                pass  # Index might already exist
            
            return True
        except Exception as e:
            print(f"[ERROR] Collection setup failed: {e}")
            return False
    
    def embed_text(self, text: str) -> list:
        """Generate embeddings for text using sentence transformers"""
        if not self.embedding_model:
            return []
        
        try:
            vector = self.embedding_model.encode([text], normalize_embeddings=True)
            return vector[0].tolist()
        except Exception as e:
            print(f"[ERROR] Text embedding failed: {e}")
            return []
    
    def build_trimester_filter(self, weeks_pregnant: int):
        """Build trimester filter for vector search"""
        if not self.client:
            return None
        
        if weeks_pregnant <= 0:
            return None
        
        trimester = "first" if weeks_pregnant <= 13 else ("second" if weeks_pregnant <= 27 else "third")
        
        return Filter(
            should=[
                FieldCondition(key="trimester", match=MatchValue(value=trimester)),
                FieldCondition(key="trimester", match=MatchValue(value="all")),
            ]
        )
    
    def search_knowledge(self, query_text: str, weeks_pregnant: int) -> list:
        """Search pregnancy knowledge base using vector similarity"""
        if not self.client or not self.embedding_model:
            return []
        
        try:
            # Generate query embedding
            query_vector = self.embed_text(query_text)
            if not query_vector:
                return []
            
            # Build trimester filter
            trimester_filter = self.build_trimester_filter(weeks_pregnant)
            
            # Search Qdrant
            results = self.client.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=query_vector,
                limit=TOP_K,
                query_filter=trimester_filter,
                with_payload=True,
                score_threshold=RETRIEVAL_MIN_SCORE
            )
            
            # Format results
            suggestions = []
            for hit in results:
                payload = hit.payload or {}
                suggestions.append({
                    "id": str(hit.id),
                    "text": payload.get("text", ""),
                    "metadata": {
                        "source": payload.get("source", ""),
                        "tags": payload.get("tags", []),
                        "triage": payload.get("triage", ""),
                        "trimester": payload.get("trimester", ""),
                    },
                    "score": float(hit.score) if hit.score is not None else None,
                })
            
            return suggestions
        except Exception as e:
            print(f"[ERROR] Knowledge search failed: {e}")
            return []


# Global quantum service instance - import this for use across the app
quantum_service = QuantumVectorService()


