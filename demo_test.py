#!/usr/bin/env python
"""
Script de test interactif pour démonstration
"""
import os
import sys
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rag.models import Document, QueryLog
from rag.agents.planner import PlannerAgent
from rag.agents.executor import ExecutorAgent
from rag.agents.critic import CriticAgent
from rag.llm.ollama import OllamaClient

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def print_step(step, text):
    print(f"\n[Étape {step}] {text}")
    print("-" * 60)

def test_full_pipeline():
    """Test complet du pipeline avec un document réel"""
    
    print_header("TEST COMPLET DU PIPELINE RAG")
    
    # Vérifier qu'il y a des documents
    doc = Document.objects.filter(indexed=True).first()
    
    if not doc:
        print("❌ Aucun document indexé trouvé!")
        print("Veuillez d'abord importer un document via l'interface web.")
        return
    
    print(f"📄 Document sélectionné: {doc.title}")
    print(f"   Chunks: {doc.chunks.count()}")
    print(f"   Indexé le: {doc.uploaded_at.strftime('%d/%m/%Y %H:%M')}")
    
    # Question de test
    question = "Qu'est-ce que le RAG ?"
    print(f"\n❓ Question: {question}")
    
    # Étape 1: Planner
    print_step(1, "PLANNER AGENT - Analyse de la question")
    start = time.time()
    planner = PlannerAgent()
    plan_result = planner.analyze(question)
    planner_time = time.time() - start
    
    print(f"   Mots-clés extraits: {plan_result['keywords']}")
    print(f"   Question reformulée: {plan_result['reformulated']}")
    print(f"   ⏱️  Temps: {planner_time*1000:.0f}ms")
    
    # Étape 2: Executor
    print_step(2, "EXECUTOR AGENT - Recherche FAISS")
    start = time.time()
    executor = ExecutorAgent(str(doc.id))
    exec_result = executor.retrieve(question, plan_result['keywords'])
    executor_time = time.time() - start
    
    print(f"   Chunks récupérés: {exec_result['count']}")
    print(f"   Score moyen: {exec_result['avg_score']:.3f}")
    for i, chunk in enumerate(exec_result['chunks'], 1):
        print(f"   Source {i}: score = {chunk['score']:.3f}")
    print(f"   ⏱️  Temps: {executor_time*1000:.0f}ms")
    
    # Étape 3: LLM
    print_step(3, "LLM OLLAMA - Génération de la réponse")
    start = time.time()
    ollama = OllamaClient()
    answer = ollama.generate_with_chunks(question, exec_result['chunks'])
    llm_time = time.time() - start
    
    print(f"   Réponse générée ({len(answer)} caractères):")
    print(f"   {answer[:200]}...")
    print(f"   ⏱️  Temps: {llm_time:.1f}s")
    
    # Étape 4: Critic
    print_step(4, "CRITIC AGENT - Validation de cohérence")
    start = time.time()
    critic = CriticAgent()
    validation = critic.validate(answer, exec_result['chunks'])
    critic_time = time.time() - start
    
    print(f"   Validation: {'✅ Validé' if validation['is_valid'] else '❌ Non validé'}")
    print(f"   Score de confiance: {validation['confidence']:.3f} ({validation['confidence']*100:.1f}%)")
    print(f"   Raison: {validation['reason']}")
    print(f"   ⏱️  Temps: {critic_time*1000:.0f}ms")
    
    # Résumé
    total_time = planner_time + executor_time + llm_time + critic_time
    print_header("RÉSUMÉ DU PIPELINE")
    
    print(f"⏱️  Temps total: {total_time:.2f}s")
    print(f"   - Planner:  {planner_time*1000:>6.0f}ms ({planner_time/total_time*100:>5.1f}%)")
    print(f"   - Executor: {executor_time*1000:>6.0f}ms ({executor_time/total_time*100:>5.1f}%)")
    print(f"   - LLM:      {llm_time:>6.1f}s  ({llm_time/total_time*100:>5.1f}%)")
    print(f"   - Critic:   {critic_time*1000:>6.0f}ms ({critic_time/total_time*100:>5.1f}%)")
    
    print(f"\n✅ Score de confiance final: {validation['confidence']*100:.1f}%")
    print(f"✅ Validation: {'Réussie' if validation['is_valid'] else 'Échouée'}")
    
    return validation['confidence'] >= 0.5

def show_statistics():
    """Affiche les statistiques d'utilisation"""
    
    print_header("STATISTIQUES D'UTILISATION")
    
    doc_count = Document.objects.count()
    indexed_count = Document.objects.filter(indexed=True).count()
    query_count = QueryLog.objects.count()
    
    print(f"📊 Documents:")
    print(f"   Total: {doc_count}")
    print(f"   Indexés: {indexed_count}")
    
    print(f"\n📊 Requêtes:")
    print(f"   Total: {query_count}")
    
    if query_count > 0:
        avg_confidence = QueryLog.objects.aggregate(
            avg_conf=django.db.models.Avg('confidence_score')
        )['avg_conf']
        validated_count = QueryLog.objects.filter(critic_validation=True).count()
        
        print(f"   Confiance moyenne: {avg_confidence:.3f} ({avg_confidence*100:.1f}%)")
        print(f"   Validées: {validated_count}/{query_count} ({validated_count/query_count*100:.1f}%)")
        
        print(f"\n📊 Dernières requêtes:")
        for query in QueryLog.objects.order_by('-created_at')[:5]:
            status = "✅" if query.critic_validation else "❌"
            print(f"   {status} {query.question[:50]}... ({query.confidence_score*100:.1f}%)")

def main():
    """Menu principal"""
    
    print_header("🤖 AGENTIC GRAPH-RAG 3.0 - TEST INTERACTIF")
    
    print("Options:")
    print("  1. Test complet du pipeline")
    print("  2. Afficher les statistiques")
    print("  3. Les deux")
    print("  0. Quitter")
    
    choice = input("\nVotre choix: ").strip()
    
    if choice == "1":
        success = test_full_pipeline()
        print("\n" + "="*60)
        if success:
            print("✅ TEST RÉUSSI - Le système fonctionne parfaitement!")
        else:
            print("⚠️  TEST PARTIEL - Score de confiance faible")
        print("="*60)
        
    elif choice == "2":
        show_statistics()
        
    elif choice == "3":
        success = test_full_pipeline()
        show_statistics()
        print("\n" + "="*60)
        if success:
            print("✅ SYSTÈME VALIDÉ - Prêt pour la présentation!")
        else:
            print("⚠️  Vérifier les résultats ci-dessus")
        print("="*60)
        
    elif choice == "0":
        print("\nAu revoir!")
        
    else:
        print("\n❌ Choix invalide")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
