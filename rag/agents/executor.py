"""
Agent Executor: Récupère les chunks pertinents via FAISS
"""
from typing import List, Dict
from rag.retrieval.vector import VectorRetriever

class ExecutorAgent:
    """Lance la recherche vectorielle et récupère les chunks"""
    
    def __init__(self, document_id: str):
        self.retriever = VectorRetriever(document_id)
    
    def retrieve(self, question: str, keywords: List[str], top_k: int = 3) -> Dict:
        """
        Récupère les chunks les plus pertinents
        """
        # Utilise la question complète pour la recherche sémantique
        results = self.retriever.search(question, top_k=top_k)
        
        return {
            'chunks': results,
            'count': len(results),
            'avg_score': sum(r['score'] for r in results) / len(results) if results else 0.0
        }
