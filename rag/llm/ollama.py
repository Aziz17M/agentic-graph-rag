"""
Client Ollama pour génération de réponses avec LLM local
"""
import requests
from django.conf import settings
from typing import List, Dict

class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
    
    def generate(self, prompt: str, context: str = "") -> str:
        """
        Génère une réponse avec Ollama
        """
        full_prompt = f"{context}\n\nQuestion: {prompt}\n\nRéponse:" if context else prompt
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('response', '').strip()
        except Exception as e:
            return f"Erreur lors de la génération: {str(e)}"
    
    def generate_with_chunks(self, question: str, chunks: List[Dict]) -> str:
        """
        Génère une réponse basée sur les chunks récupérés
        """
        context = "=== CONTEXTE DU DOCUMENT ===\n\n"
        for i, chunk in enumerate(chunks, 1):
            context += f"[Source {i}] {chunk['content']}\n\n"
        
        context += "=== INSTRUCTIONS ===\n"
        context += "1. Réponds à la question en utilisant UNIQUEMENT les informations du contexte ci-dessus\n"
        context += "2. Cite les sources utilisées en mentionnant [Source X]\n"
        context += "3. Si l'information n'est pas dans le contexte, dis 'L'information n'est pas disponible dans le document'\n"
        context += "4. Sois précis et concis (2-4 phrases maximum)\n"
        context += "5. Utilise les termes exacts du document quand c'est pertinent\n\n"
        
        return self.generate(question, context)
