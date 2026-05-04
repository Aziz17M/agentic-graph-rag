"""
Debug script to test the question answering
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rag.models import Document, Chunk
from rag.agents.planner import PlannerAgent
from rag.agents.executor import ExecutorAgent
from rag.agents.critic import CriticAgent
from rag.llm.ollama import OllamaClient

# Get the last document
doc = Document.objects.last()
if not doc:
    print("❌ No document found. Please upload a document first.")
    exit(1)

print(f"📄 Document: {doc.title}")
print(f"📊 Chunks: {doc.chunks.count()}")

# Test question
question = "c'est quoi l'intelligence artificielle ?"
print(f"\n❓ Question: {question}")

# Step 1: Planner
print("\n" + "="*60)
print("STEP 1: PLANNER")
print("="*60)
planner = PlannerAgent()
plan_result = planner.analyze(question)
print(f"Keywords: {plan_result['keywords']}")
print(f"Reformulated: {plan_result['reformulated']}")

# Step 2: Executor (without MCP first to debug)
print("\n" + "="*60)
print("STEP 2: EXECUTOR (Direct, no MCP)")
print("="*60)
executor = ExecutorAgent(str(doc.id), use_mcp=False)

# Load chunks
chunks = Chunk.objects.filter(document_id=doc.id).order_by('chunk_index')
executor.retriever.chunks = [c.content for c in chunks]
print(f"Loaded {len(executor.retriever.chunks)} chunks")

# Try vector search
print("\n--- Vector Search ---")
try:
    vector_results = executor.retriever.vector_retriever.search(question, top_k=3)
    print(f"✅ Found {len(vector_results)} results")
    for i, r in enumerate(vector_results, 1):
        print(f"  {i}. Score: {r['score']:.3f} - {r['content'][:100]}...")
except Exception as e:
    print(f"❌ Error: {e}")

# Try graph search
print("\n--- Graph Search ---")
try:
    graph_results = executor.retriever.graph_retriever.search_graph(question, top_k=3)
    print(f"✅ Found {len(graph_results)} results")
    for i, r in enumerate(graph_results, 1):
        idx = r['chunk_index']
        if idx < len(executor.retriever.chunks):
            content = executor.retriever.chunks[idx]
            print(f"  {i}. Score: {r['score']:.3f} - {content[:100]}...")
except Exception as e:
    print(f"❌ Error: {e}")

# Try hybrid search
print("\n--- Hybrid Search ---")
try:
    hybrid_results = executor.retriever.search(question, top_k=3)
    print(f"✅ Found {len(hybrid_results)} results")
    for i, r in enumerate(hybrid_results, 1):
        print(f"  {i}. Hybrid: {r['score']:.3f} | Vector: {r.get('vector_score', 0):.3f} | Graph: {r.get('graph_score', 0):.3f}")
        print(f"     {r['content'][:100]}...")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Step 3: LLM
print("\n" + "="*60)
print("STEP 3: LLM GENERATION")
print("="*60)
try:
    exec_result = executor.retrieve(question, plan_result['keywords'], method='hybrid')
    if exec_result['chunks']:
        ollama = OllamaClient()
        answer = ollama.generate_with_chunks(question, exec_result['chunks'])
        print(f"Answer: {answer[:200]}...")
        
        # Step 4: Critic
        print("\n" + "="*60)
        print("STEP 4: CRITIC")
        print("="*60)
        critic = CriticAgent()
        validation = critic.validate(answer, exec_result['chunks'])
        print(f"Is Valid: {validation['is_valid']}")
        print(f"Confidence: {validation['confidence']:.3f}")
        print(f"Keyword Overlap: {validation.get('keyword_overlap', 0):.3f}")
        print(f"FAISS Score: {validation.get('faiss_score', 0):.3f}")
        print(f"Reason: {validation['reason']}")
    else:
        print("❌ No chunks retrieved!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
