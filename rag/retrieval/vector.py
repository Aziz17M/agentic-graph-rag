"""
Indexation et recherche vectorielle avec FAISS
"""
import faiss
import numpy as np
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict
from django.conf import settings

class VectorRetriever:
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index_path = Path(settings.MEDIA_ROOT) / f"faiss_{document_id}.index"
        self.chunks_path = Path(settings.MEDIA_ROOT) / f"chunks_{document_id}.pkl"
        self.index = None
        self.chunks = []
    
    def create_chunks(self, text: str, chunk_size: int = 500) -> List[str]:
        """Découpe le texte en chunks de mots"""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks
    
    def index_chunks(self, chunks: List[str]) -> None:
        """Encode et indexe les chunks dans FAISS"""
        self.chunks = chunks
        embeddings = self.model.encode(chunks, show_progress_bar=False)
        embeddings = np.array(embeddings).astype('float32')
        
        # Création de l'index FAISS
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product (similarité cosinus)
        
        # Normalisation pour similarité cosinus
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
        
        # Sauvegarde
        faiss.write_index(self.index, str(self.index_path))
        with open(self.chunks_path, 'wb') as f:
            pickle.dump(self.chunks, f)
    
    def load_index(self) -> bool:
        """Charge l'index FAISS existant"""
        if self.index_path.exists() and self.chunks_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.chunks_path, 'rb') as f:
                self.chunks = pickle.load(f)
            return True
        return False
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Recherche les chunks les plus similaires"""
        if not self.load_index():
            return []
        
        query_embedding = self.model.encode([query], show_progress_bar=False)
        query_embedding = np.array(query_embedding).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        scores, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks):
                results.append({
                    'content': self.chunks[idx],
                    'score': float(score),
                    'index': int(idx)
                })
        
        return results
