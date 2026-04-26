"""
Agent Planner: Analyse et reformule la question
"""
import re
from typing import Dict, List

class PlannerAgent:
    """Analyse la question et extrait les mots-clés pertinents"""
    
    STOP_WORDS = {
        'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'à', 
        'dans', 'pour', 'par', 'sur', 'avec', 'est', 'sont', 'a', 'ont',
        'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'is', 'are'
    }
    
    def analyze(self, question: str) -> Dict:
        """
        Analyse la question et retourne:
        - keywords: mots-clés extraits
        - reformulated: question reformulée (simplifiée)
        """
        # Nettoyage
        clean_question = re.sub(r'[^\w\s]', ' ', question.lower())
        words = clean_question.split()
        
        # Extraction des mots-clés (sans stop words)
        keywords = [w for w in words if w not in self.STOP_WORDS and len(w) > 2]
        
        # Reformulation simple
        reformulated = ' '.join(keywords) if keywords else question
        
        return {
            'original': question,
            'keywords': keywords[:5],  # Top 5 mots-clés
            'reformulated': reformulated
        }
