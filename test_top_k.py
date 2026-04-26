#!/usr/bin/env python
"""
Script pour tester différentes valeurs de top_k
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rag.agents.executor import ExecutorAgent
from rag.agents.planner import PlannerAgent
from rag.llm.ollama import OllamaClient
from rag.models import Document

def test_top_k(document_id, question, top_k_values=[1, 2, 3, 5]):
    """Teste différentes valeurs de top_k"""
    
    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"{'='*60}\n")
    
    planner = PlannerAgent()
    plan_result = planner.analyze(question)
    
    for k in top_k_values:
        print(f"\n--- Test avec top_k = {k} ---")
        
        executor = ExecutorAgent(document_id)
        exec_result = executor.retrieve(question, plan_result['keywords'], top_k=k)
        
        print(f"Nombre de chunks récupérés: {exec_result['count']}")
        print(f"Score moyen: {exec_result['avg_score']:.3f}")
        
        # Afficher les scores
        for i, chunk in enumerate(exec_result['chunks'], 1):
            print(f"  Source {i}: score = {chunk['score']:.3f}")
        
        # Générer la réponse
        ollama = OllamaClient()
        answer = ollama.generate_with_chunks(question, exec_result['chunks'])
        
        print(f"\nRéponse (premiers 200 caractères):")
        print(f"{answer[:200]}...")
        print(f"\nLongueur réponse: {len(answer)} caractères")

if __name__ == "__main__":
    # Récupérer le premier document
    doc = Document.objects.filter(indexed=True).first()
    
    if not doc:
        print("❌ Aucun document indexé trouvé!")
        print("Importez d'abord un document via l'interface web.")
        sys.exit(1)
    
    print(f"📄 Document: {doc.title}")
    
    # Tester avec différentes valeurs
    test_top_k(
        str(doc.id),
        "Qu'est-ce que le RAG ?",
        top_k_values=[1, 2, 3, 5]
    )
    
    print("\n" + "="*60)
    print("✅ Tests terminés!")
    print("="*60)
