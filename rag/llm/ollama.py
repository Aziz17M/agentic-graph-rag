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
        context = "Contexte extrait du document:\n\n"
        for i, chunk in enumerate(chunks, 1):
            context += f"[Source {i}] {chunk['content']}\n\n"
        
        context += "Instructions: Réponds à la question en te basant UNIQUEMENT sur le contexte ci-dessus. "
        context += "Cite les sources utilisées ([Source X])."
        
        return self.generate(question, context)
