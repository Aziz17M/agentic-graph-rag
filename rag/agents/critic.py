"""
Agent Critic: Vérifie la cohérence de la réponse
"""
from typing import Dict, List

class CriticAgent:
    """Valide que la réponse est cohérente avec les sources"""
    
    def validate(self, answer: str, chunks: List[Dict]) -> Dict:
        """
        Vérifie que la réponse contient des éléments des chunks sources
        """
        if not answer or not chunks:
            return {
                'is_valid': False,
                'confidence': 0.0,
                'reason': 'Réponse ou chunks manquants'
            }
        
        # Extraction des mots significatifs de la réponse
        answer_words = set(answer.lower().split())
        
        # Vérification de la présence de mots des chunks dans la réponse
        overlap_scores = []
        for chunk in chunks:
            chunk_words = set(chunk['content'].lower().split())
            if chunk_words:
                overlap = len(answer_words & chunk_words) / len(chunk_words)
                overlap_scores.append(overlap)
        
        avg_overlap = sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0.0
        
        # Validation basique: au moins 5% de chevauchement
        is_valid = avg_overlap > 0.05
        
        # Score de confiance basé sur le chevauchement et les scores FAISS
        avg_faiss_score = sum(c['score'] for c in chunks) / len(chunks)
        confidence = (avg_overlap * 0.4 + avg_faiss_score * 0.6)
        
        return {
            'is_valid': is_valid,
            'confidence': round(confidence, 3),
            'overlap': round(avg_overlap, 3),
            'reason': 'Validation réussie' if is_valid else 'Chevauchement insuffisant'
        }
