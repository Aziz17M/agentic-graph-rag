"""
Agent Critic: Vérifie la cohérence de la réponse
"""
from typing import Dict, List
import re

class CriticAgent:
    """Valide que la réponse est cohérente avec les sources"""
    
    def _extract_keywords(self, text: str) -> set:
        """Extrait les mots significatifs (>3 caractères, pas de stop words)"""
        # Mots vides français courants
        stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'mais',
            'dans', 'pour', 'par', 'sur', 'avec', 'sans', 'est', 'sont', 'être',
            'avoir', 'que', 'qui', 'quoi', 'dont', 'où', 'ce', 'cette', 'ces',
            'son', 'sa', 'ses', 'leur', 'leurs', 'mon', 'ma', 'mes', 'ton', 'ta',
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might',
            'can', 'this', 'that', 'these', 'those', 'a', 'an', 'as', 'by', 'from'
        }
        
        # Nettoyage et extraction
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = {w for w in words if len(w) > 3 and w not in stop_words}
        return keywords
    
    def validate(self, answer: str, chunks: List[Dict]) -> Dict:
        """
        Vérifie que la réponse est cohérente avec les sources
        Utilise plusieurs critères pour une évaluation robuste
        """
        if not answer or not chunks:
            return {
                'is_valid': False,
                'confidence': 0.0,
                'reason': 'Réponse ou chunks manquants'
            }
        
        # Critère 1: Longueur de la réponse (réponse substantielle)
        answer_length = len(answer.split())
        length_score = min(answer_length / 20, 1.0)  # Max à 20 mots
        
        # Critère 2: Mots-clés significatifs partagés
        answer_keywords = self._extract_keywords(answer)
        
        keyword_overlaps = []
        for chunk in chunks:
            chunk_keywords = self._extract_keywords(chunk['content'])
            if chunk_keywords:
                overlap = len(answer_keywords & chunk_keywords) / max(len(chunk_keywords), 1)
                keyword_overlaps.append(overlap)
        
        avg_keyword_overlap = sum(keyword_overlaps) / len(keyword_overlaps) if keyword_overlaps else 0.0
        
        # Critère 3: Score FAISS moyen (pertinence des chunks)
        avg_faiss_score = sum(c['score'] for c in chunks) / len(chunks)
        
        # Critère 4: Détection de phrases d'erreur
        error_phrases = [
            'je ne trouve pas', 'pas d\'information', 'ne sais pas',
            'aucune information', 'pas mentionné', 'pas de réponse',
            'cannot find', 'no information', 'not mentioned', 'don\'t know',
            'erreur lors de', 'error during'
        ]
        has_error = any(phrase in answer.lower() for phrase in error_phrases)
        error_penalty = 0.5 if has_error else 1.0
        
        # Critère 5: Présence de citations [Source X]
        has_citations = '[source' in answer.lower() or 'source' in answer.lower()
        citation_bonus = 1.1 if has_citations else 1.0
        
        # Calcul du score de confiance pondéré
        confidence = (
            avg_faiss_score * 0.40 +           # 40% - Pertinence FAISS
            avg_keyword_overlap * 0.30 +       # 30% - Mots-clés partagés
            length_score * 0.15 +              # 15% - Longueur réponse
            (1.0 if not has_error else 0.0) * 0.15  # 15% - Pas d'erreur
        ) * citation_bonus * error_penalty
        
        # Validation: confiance > 30% et pas de phrase d'erreur
        is_valid = confidence > 0.30 and not has_error
        
        return {
            'is_valid': is_valid,
            'confidence': round(min(confidence, 1.0), 3),
            'keyword_overlap': round(avg_keyword_overlap, 3),
            'faiss_score': round(avg_faiss_score, 3),
            'reason': 'Validation réussie' if is_valid else 'Confiance insuffisante ou erreur détectée'
        }
