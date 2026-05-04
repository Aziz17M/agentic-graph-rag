"""
Test script for Graph Retrieval and MCP Protocol
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rag.retrieval.graph import GraphRetriever
from rag.retrieval.hybrid import HybridRetriever
from rag.mcp.client import MCPClient


def test_graph_retrieval():
    """Test graph-based retrieval"""
    print("=" * 60)
    print("TEST 1: Graph Retrieval")
    print("=" * 60)
    
    # Sample text
    text = """
    RAG is a Retrieval-Augmented Generation system. RAG uses vector search.
    FAISS is a library for vector similarity. FAISS implements efficient search.
    Django is a web framework. Django uses Python programming language.
    MCP is the Model Context Protocol. MCP enables interoperability.
    """
    
    # Create graph retriever
    graph = GraphRetriever("test-graph")
    
    # Create chunks
    chunks = text.strip().split('\n')
    chunks = [c.strip() for c in chunks if c.strip()]
    
    # Build graph
    print(f"\n📊 Building graph from {len(chunks)} chunks...")
    graph.build_graph(chunks)
    
    # Get stats
    stats = graph.get_graph_stats()
    print(f"✅ Graph built:")
    print(f"   - Nodes (entities): {stats['nodes']}")
    print(f"   - Edges (relationships): {stats['edges']}")
    print(f"   - Density: {stats['density']:.3f}")
    print(f"   - Avg degree: {stats['avg_degree']:.2f}")
    
    # Test search
    query = "What is RAG?"
    print(f"\n🔍 Searching for: '{query}'")
    results = graph.search_graph(query, top_k=2)
    
    print(f"✅ Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"   {i}. Chunk {result['chunk_index']} - Score: {result['score']:.3f}")
    
    return True


def test_hybrid_retrieval():
    """Test hybrid retrieval (vector + graph)"""
    print("\n" + "=" * 60)
    print("TEST 2: Hybrid Retrieval (Vector + Graph)")
    print("=" * 60)
    
    # Sample text
    text = """
    Artificial Intelligence is transforming technology. AI uses machine learning algorithms.
    Machine learning requires large datasets. Datasets contain training examples.
    Neural networks are powerful models. Networks learn from data patterns.
    Deep learning is a subset of machine learning. Deep learning uses multiple layers.
    """
    
    # Create hybrid retriever
    hybrid = HybridRetriever("test-hybrid")
    
    # Create chunks
    chunks = text.strip().split('.')
    chunks = [c.strip() + '.' for c in chunks if c.strip()]
    
    print(f"\n📊 Indexing {len(chunks)} chunks with hybrid method...")
    hybrid.index_document(chunks)
    
    # Get stats
    stats = hybrid.get_retrieval_stats()
    print(f"✅ Hybrid index created:")
    print(f"   - Vector: {stats['vector']['chunks']} chunks indexed")
    print(f"   - Graph: {stats['graph']['nodes']} nodes, {stats['graph']['edges']} edges")
    
    # Test search
    query = "What is machine learning?"
    print(f"\n🔍 Hybrid search for: '{query}'")
    results = hybrid.search(query, top_k=3, vector_weight=0.6, graph_weight=0.4)
    
    print(f"✅ Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n   {i}. Hybrid Score: {result['score']:.3f}")
        print(f"      - Vector: {result['vector_score']:.3f}")
        print(f"      - Graph: {result['graph_score']:.3f}")
        print(f"      - Content: {result['content'][:80]}...")
    
    return True


def test_mcp_protocol():
    """Test MCP protocol"""
    print("\n" + "=" * 60)
    print("TEST 3: MCP Protocol")
    print("=" * 60)
    
    # Create MCP client
    client = MCPClient("rag-server")
    
    print(f"\n🔗 MCP Client initialized")
    print(f"   - Server: {client.server_name}")
    print(f"   - Session ID: {client.session_id[:16]}...")
    
    # Test 1: Analyze question
    print(f"\n📝 Test MCP Tool: analyze_question")
    response = client.call_tool(
        tool_name="analyze_question",
        arguments={"question": "What is the RAG system?"},
        context={"test": True}
    )
    
    if "result" in response:
        result = response["result"]["content"]
        print(f"✅ Tool executed successfully:")
        print(f"   - Keywords: {result['keywords']}")
        print(f"   - Reformulated: {result['reformulated']}")
        print(f"   - Call ID: {response['id'][:16]}...")
    else:
        print(f"❌ Error: {response.get('error', {}).get('message')}")
    
    # Test 2: Read resource
    print(f"\n📚 Test MCP Resource: rag://stats")
    response = client.read_resource("rag://stats")
    
    if "result" in response:
        print(f"✅ Resource read successfully:")
        content = response["result"]["contents"][0]
        print(f"   - URI: {content['uri']}")
        print(f"   - MIME: {content['mimeType']}")
        print(f"   - Content: {content['text'][:100]}...")
    else:
        print(f"❌ Error: {response.get('error', {}).get('message')}")
    
    # Get session info
    session_info = client.get_session_info()
    print(f"\n📊 Session Info:")
    print(f"   - Total calls: {session_info['total_calls']}")
    print(f"   - Session ID: {session_info['session_id'][:16]}...")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "🚀" * 30)
    print("TESTING GRAPH RETRIEVAL & MCP PROTOCOL")
    print("🚀" * 30 + "\n")
    
    tests = [
        ("Graph Retrieval", test_graph_retrieval),
        ("Hybrid Retrieval", test_hybrid_retrieval),
        ("MCP Protocol", test_mcp_protocol)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} FAILED: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Graph-RAG with MCP is working!")
    else:
        print("\n⚠️ Some tests failed. Check the output above.")


if __name__ == "__main__":
    main()
