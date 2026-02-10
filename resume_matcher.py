import os
import json
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import endee

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class ResumeMatcher:
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2', base_url: Optional[str] = None):
        """Initialize the matcher with embedding model and Endee vector DB."""
        print(f"Loading model {model_name}...")
        self.model = SentenceTransformer(model_name)
        
        # Initialize Endee Client
        # Use provided base_url, or env var, or default local
        self.base_url = base_url or os.getenv("ENDEE_URL", "http://127.0.0.1:8080/api/v1")
        self.client = endee.Endee()
        if self.base_url:
            self.client.set_base_url(self.base_url)
        
        self.index_name = "resumes_idx"
        self.index = None
        
        # Try to get existing index, or create if missing
        try:
            self.index = self.client.get_index(self.index_name)
            # Check if index works or needs creation (Endee might throw if not found)
        except Exception:
            # Index likely doesn't exist, create it
            try:
                self.client.create_index(
                    name=self.index_name,
                    dimension=384,
                    space_type='cosine'
                )
                self.index = self.client.get_index(self.index_name)
            except Exception as e:
                print(f"Warning: Could not create/get index: {e}")

    def reset_index(self):
        """Helper to wipe and recreate index (used by demo)."""
        try:
            self.client.delete_index(self.index_name)
        except Exception:
            pass
            
        self.client.create_index(
            name=self.index_name,
            dimension=384,
            space_type='cosine'
        )
        self.index = self.client.get_index(self.index_name)

    def ingest(self, json_path: str):
        """Load resumes from JSON and index them in Endee."""
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Data file not found: {json_path}")
            
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        print(f"Embedding {len(data)} resumes...")
        
        # Enrich the embedding context by including Role and Skills explicitly
        documents = []
        for item in data:
            # Create a rich semantic representation
            rich_text = f"Role: {item['role']}. Skills: {', '.join(item['skills'])}. Summary: {item['summary']}"
            documents.append(rich_text)
            
        embeddings = self.model.encode(documents).tolist()
        
        upsert_data = []
        for i, item in enumerate(data):
            upsert_data.append({
                "id": item['id'],
                "vector": embeddings[i],
                "meta": {
                    "role": item['role'],
                    "years": item['years'],
                    "skills": item['skills'],
                    "summary": item['summary']
                },
                "filter": {
                    "role": item['role'],
                    "years": item['years'],
                    "skills": item['skills']
                }
            })
        
        if self.index:
            self.index.upsert(upsert_data)
            print(f"Indexed {len(data)} documents successfully.")
        else:
            print("Error: Index not initialized.")

    def query(self, text: str, filters: Optional[Dict[str, Any]] = None, top_k: int = 5) -> List[Dict]:
        """
        Search for resumes matching the query text and filters.
        """
        if not text.strip() and not filters:
            return []

        if not text.strip():
             # If just filtering without text query, fetching might be harder with vector search
             # But let's try to query with a dummy vector or rely on pure filter if possible
             # For this task, we assume text part is key or we use a zero vector if supported.
             # Better: return empty or handle if you want to support "all backend devs" without vector.
             # Assuming text is required for semantic search.
             return []

        if not self.index:
            return []

        query_vector = self.model.encode([text]).tolist()[0]
        
        # Endee expects filter as a list of dicts based on schema
        # However, we've observed server-side filtering might be permissive or not working as expected.
        # We will fetch a larger pool ($top_k * 4) and filter client-side to ensure accuracy.
        endee_filter = [filters] if filters else None

        try:
            # Fetch more candidates to allow for post-filtering
            results = self.index.query(
                vector=query_vector,
                top_k=top_k * 5, 
                filter=endee_filter
            )
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
            
        formatted = self._format_results(results)
        
        if not filters:
            return formatted[:top_k]
            
        # Strict Client-Side Filtering
        filtered_results = []
        for item in formatted:
            matches = True
            for key, condition in filters.items():
                # specific override for nested dict filters usually passed as one level in resumes
                # item is flat: role, years, skills
                item_value = item.get(key)
                
                if isinstance(condition, dict):
                    if '$gte' in condition and item_value is not None:
                        if not (item_value >= condition['$gte']):
                            matches = False
                            break
                    if '$lte' in condition and item_value is not None:
                         if not (item_value <= condition['$lte']):
                            matches = False
                            break
                    if '$eq' in condition:
                        if item_value != condition['$eq']:
                            matches = False
                            break
                    if '$in' in condition and item_value is not None:
                        # item_value could be list (skills) or scalar
                        required = condition['$in']
                        if isinstance(item_value, list):
                            # Check if ANY of required skills are in candidate skills (overlap)
                            # Or ALL? "filters: skills in [...]" usually implies candidates having one of them
                            if not any(req in item_value for req in required):
                                matches = False
                                break
                        else:
                            if item_value not in required:
                                matches = False
                                break
                else:
                    # Direct equality
                    if item_value != condition:
                        matches = False
                        break
            
            if matches:
                filtered_results.append(item)
                
        return filtered_results[:top_k]

    def _format_results(self, results) -> List[Dict]:
        """Format Endee results into clean list of dicts."""
        parsed = []
        if not results:
            return []
            
        for res in results:
            meta = res.get('meta', {})
            parsed.append({
                'id': res.get('id'),
                'score': round(res.get('similarity', 0), 4),
                'role': meta.get('role'),
                'years': meta.get('years'),
                'skills': meta.get('skills'),
                'summary': meta.get('summary')
            })
            
        return parsed

if __name__ == "__main__":
    matcher = ResumeMatcher()
    matcher.ingest("data/resumes.json")
    print(matcher.query("React developer"))
