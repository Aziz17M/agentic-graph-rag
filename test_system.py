#!/usr/bin/env python
"""
Script de test pour vérifier que tous les composants fonctionnent
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rag.agents.planner import PlannerAgent
from rag.agents.executor import ExecutorAgent
from rag.agents.critic import CriticAgent
from rag.llm.ollama import OllamaClient
from rag.mcp.tools import MCPTools
from rag.retrieval.vector import VectorRetriever
import requests

def test_planner():
    """Test du Planner Agent"""
    print("\n🧪 Test 1: Planner Agent")
    planner = PlannerAgent()
    result = planner.analyze("Qu'est-ce que le machine learning ?")
    print(f"   ✅ Mots-clés extraits: {result['keywords']}")
    print(f"   ✅ Question reformulée: {result['reformulated']}")
    assert len(result['keywords']) > 0, "Aucun mot-clé extrait"
    print("   ✅ Planner fonctionne correctement")

def test_vector_retriever():
    """Test du VectorRetriever"""
    print("\n🧪 Test 2: Vector Retriever (FAISS)")
    retriever = VectorRetriever("test-doc-id")
    
    # Création de chunks de test
    test_chunks = [
        "Le machine learning est une branche de l'intelligence artificielle.",
        "FAISS permet de faire des recherches vectorielles rapides.",
        "Django est un framework web Python populaire."
    ]
    
    print(f"   ✅ Création de {len(test_chunks)} chunks de test")
    retriever.index_chunks(test_chunks)
    print("   ✅ Indexation FAISS réussie")
    
    # Test de recherche
    results = retriever.search("intelligence artificielle", top_k=2)
    print(f"   ✅ Recherche effectuée: {len(results)} résultats")
    print(f"   ✅ Meilleur score: {results[0]['score']:.3f}")
    assert len(results) > 0, "Aucun résultat trouvé"
    print("   ✅ Vector Retriever fonctionne correctement")

def test_critic():
    """Test du Critic Agent"""
    print("\n🧪 Test 3: Critic Agent")
    critic = CriticAgent()
    
    test_chunks = [
        {'content': 'Le machine learning utilise des algorithmes', 'score': 0.85},
        {'content': 'Les réseaux de neurones sont importants', 'score': 0.75}
    ]
    
    answer = "Le machine learning utilise des algorithmes et des réseaux de neurones"
    result = critic.validate(answer, test_chunks)
    
    print(f"   ✅ Validation: {result['is_valid']}")
    print(f"   ✅ Score de confiance: {result['confidence']:.3f}")
    print(f"   ✅ Raison: {result['reason']}")
    assert result['confidence'] > 0, "Score de confiance invalide"
    print("   ✅ Critic fonctionne correctement")

def test_mcp_tools():
    """Test des MCP Tools"""
    print("\n🧪 Test 4: MCP Protocol")
    
    # Test création d'appel Planner
    mcp_call = MCPTools.create_planner_call("Test question")
    print(f"   ✅ MCP Planner call créé: {mcp_call.tool_name}")
    print(f"   ✅ Trace ID: {mcp_call.trace_id[:8]}...")
    
    # Test création d'appel Executor
    mcp_call = MCPTools.create_executor_call(['test'], "question", "trace-123")
    print(f"   ✅ MCP Executor call créé: {mcp_call.tool_name}")
    
    assert mcp_call.annotations['verifiable'] == True, "Annotation incorrecte"
    print("   ✅ MCP Tools fonctionnent correctement")

def test_ollama_connection():
    """Test de la connexion Ollama"""
    print("\n🧪 Test 5: Connexion Ollama")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"   ✅ Ollama est accessible")
            print(f"   ✅ Modèles disponibles: {len(models)}")
            
            # Vérifier si llama3.2:1b est présent
            has_llama = any('llama3.2:1b' in m.get('name', '') for m in models)
            if has_llama:
                print("   ✅ llama3.2:1b est installé")
            else:
                print("   ⚠️  llama3.2:1b non trouvé, mais Ollama fonctionne")
        else:
            print("   ⚠️  Ollama répond mais avec un code d'erreur")
    except Exception as e:
        print(f"   ❌ Erreur de connexion Ollama: {e}")
        print("   ℹ️  Assurez-vous qu'Ollama est démarré: ollama serve")

def test_django_models():
    """Test des modèles Django"""
    print("\n🧪 Test 6: Modèles Django")
    from rag.models import Document, Chunk, QueryLog
    
    # Compter les objets existants
    doc_count = Document.objects.count()
    chunk_count = Chunk.objects.count()
    query_count = QueryLog.objects.count()
    
    print(f"   ✅ Documents: {doc_count}")
    print(f"   ✅ Chunks: {chunk_count}")
    print(f"   ✅ QueryLogs: {query_count}")
    print("   ✅ Base de données accessible")

def main():
    """Exécute tous les tests"""
    print("=" * 60)
    print("🚀 Test du Système Agentic Graph-RAG 3.0")
    print("=" * 60)
    
    tests = [
        ("Planner Agent", test_planner),
        ("Vector Retriever", test_vector_retriever),
        ("Critic Agent", test_critic),
        ("MCP Tools", test_mcp_tools),
        ("Ollama Connection", test_ollama_connection),
        ("Django Models", test_django_models),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n   ❌ Erreur dans {name}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Résultats: {passed} tests réussis, {failed} tests échoués")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ Tous les tests sont passés ! Le système est prêt.")
        print("🚀 Lancez le serveur: python manage.py runserver")
        print("🌐 Accédez à: http://127.0.0.1:8000/")
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
