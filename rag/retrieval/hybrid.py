"""
Hybrid Retrieval: Combines Vector (FAISS) + Graph (NetworkX)
"""
from typing import List, Dict
from .vector import VectorRetriever
from .graph import GraphRetriever


class HybridRetriever:
    """
    Combines multiple retrieval methods:
    - Vector similarity (FAISS)
    - Graph traversal (NetworkX)
    """
    
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.vector_retriever = VectorRetriever(document_id)
        self.graph_retriever = GraphRetriever(document_id)
        self.chunks = []
    
    def index_document(self, chunks: List[str]) -> None:
        """
        Index document using both vector and graph methods
        """
        self.chunks = chunks
        
        # Vector indexing
        self.vector_retriever.index_chunks(chunks)
        
        # Graph indexing
        self.graph_retriever.build_graph(chunks)
    
    def search(self, query: str, top_k: int = 3, 
               vector_weight: float = 0.6, 
               graph_weight: float = 0.4) -> List[Dict]:
        """
        Hybrid search combining vector and graph results
        
        Args:
            query: Search query
            top_k: Number of results to return
            vector_weight: Weight for vector similarity (0-1)
            graph_weight: Weight for graph relevance (0-1)
        """
        # Get vector results
        vector_results = self.vector_retriever.search(query, top_k=top_k * 2)
        
        # Get graph results
        graph_results = self.graph_retriever.search_graph(query, top_k=top_k * 2)
        
        # Combine scores
        chunk_scores = {}
        
        # Add vector scores
        for result in vector_results:
            idx = result['index']
            chunk_scores[idx] = {
                'content': result['content'],
                'vector_score': result['score'],
                'graph_score': 0.0,
                'index': idx
            }
        
        # Add graph scores
        for result in graph_results:
            idx = result['chunk_index']
            if idx not in chunk_scores:
                # Load chunk content
                if idx < len(self.chunks):
                    chunk_scores[idx] = {
                        'content': self.chunks[idx],
                        'vector_score': 0.0,
                        'graph_score': result['score'],
                        'index': idx
                    }
            else:
                chunk_scores[idx]['graph_score'] = result['score']
        
        # Normalize scores (0-1 range)
        if chunk_scores:
            max_vector = max((c['vector_score'] for c in chunk_scores.values()), default=1.0)
            max_graph = max((c['graph_score'] for c in chunk_scores.values()), default=1.0)
            
            for idx in chunk_scores:
                chunk_scores[idx]['vector_score'] /= max(max_vector, 0.01)
                chunk_scores[idx]['graph_score'] /= max(max_graph, 0.01)
        
        # Calculate hybrid score
        for idx in chunk_scores:
            v_score = chunk_scores[idx]['vector_score']
            g_score = chunk_scores[idx]['graph_score']
            chunk_scores[idx]['hybrid_score'] = (
                v_score * vector_weight + g_score * graph_weight
            )
        
        # Sort by hybrid score and return top-k
        sorted_results = sorted(
            chunk_scores.values(), 
            key=lambda x: x['hybrid_score'], 
            reverse=True
        )[:top_k]
        
        # Format results
        results = []
        for result in sorted_results:
            results.append({
                'content': result['content'],
                'score': result['hybrid_score'],
                'vector_score': result['vector_score'],
                'graph_score': result['graph_score'],
                'index': result['index'],
                'method': 'hybrid'
            })
        
        return results
    
    def get_retrieval_stats(self) -> Dict:
        """Get statistics from both retrieval methods"""
        graph_stats = self.graph_retriever.get_graph_stats()
        
        return {
            'vector': {
                'indexed': self.vector_retriever.index is not None,
                'chunks': len(self.chunks)
            },
            'graph': graph_stats,
            'hybrid': {
                'methods': ['vector', 'graph'],
                'total_chunks': len(self.chunks)
            }
        }
