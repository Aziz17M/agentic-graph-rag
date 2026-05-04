# Quick Start Guide - Graph-RAG + MCP

## What Changed?

Your project now has **REAL Graph Retrieval** and **REAL MCP Protocol**!

## New Files Created

1. `rag/retrieval/graph.py` - Knowledge graph construction and search
2. `rag/retrieval/hybrid.py` - Combines vector + graph retrieval
3. `rag/mcp/server.py` - MCP Server with tools and resources
4. `rag/mcp/client.py` - MCP Client (JSON-RPC 2.0)
5. `test_graph_mcp.py` - Tests for graph and MCP
6. `UPGRADE_SUMMARY.md` - Detailed upgrade documentation
7. `QUICK_START.md` - This file

## Files Modified

1. `rag/agents/executor.py` - Now uses hybrid retrieval + MCP
2. `rag/views.py` - Indexes with graph + uses MCP protocol
3. `templates/demo.html` - Shows graph stats + MCP info
4. `requirements.txt` - Added networkx and mcp
5. `README.md` - Updated with Graph-RAG + MCP info

## How to Test

### 1. Server is Already Running
```
http://127.0.0.1:8000/
```

### 2. Upload a Document
- Go to the web interface
- Upload a PDF or TXT file
- You'll see: "X chunks créés | Y entités | Z relations"
- This means both vector and graph indexing worked!

### 3. Ask a Question
- Select the document
- Type a question like "Qu'est-ce que le RAG?"
- Click "Lancer le pipeline RAG"
- You'll see:
  - MCP Protocol badge (green)
  - Retrieval method: hybrid
  - Vector score + Graph score for each source
  - MCP Session ID

### 4. Run Tests (Optional)
```bash
python test_graph_mcp.py
```

## What You Can Now Say in Your Presentation

✅ "We implement **Graph-RAG** with automatic entity and relationship extraction"

✅ "We use **real MCP protocol** (JSON-RPC 2.0) for agent communication"

✅ "We have **hybrid retrieval** combining vector similarity (FAISS) and graph traversal (NetworkX)"

✅ "We provide **full provenance tracing** with MCP session management"

✅ "We support **dynamic tool selection** via MCP (vector/graph/hybrid)"

✅ "We extract **7 types of relationships**: IS_A, USES, INCLUDES, REQUIRES, IMPLEMENTS, BASED_ON, CO_OCCURS"

✅ "We implement **interoperability** through standardized MCP protocol"

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│              (templates/demo.html)                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  DJANGO VIEWS                            │
│                 (rag/views.py)                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  MCP CLIENT                              │
│              (rag/mcp/client.py)                         │
│         JSON-RPC 2.0 Protocol                            │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌────────┐  ┌─────────┐  ┌────────┐
   │PLANNER │  │EXECUTOR │  │CRITIC  │
   │ Agent  │  │ Agent   │  │ Agent  │
   └────────┘  └────┬────┘  └────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
   ┌────────┐  ┌────────┐  ┌────────┐
   │VECTOR  │  │GRAPH   │  │HYBRID  │
   │FAISS   │  │NetworkX│  │Combine │
   └────────┘  └────────┘  └────────┘
        │           │           │
        └───────────┼───────────┘
                    ▼
            ┌──────────────┐
            │  LLM OLLAMA  │
            │ llama3.2:1b  │
            └──────────────┘
```

## Key Metrics

- **Entities Extracted**: Automatic (proper nouns, technical terms, keywords)
- **Relationships Detected**: 7 types
- **Retrieval Methods**: 3 (vector, graph, hybrid)
- **MCP Tools**: 5 (search_vector, search_graph, search_hybrid, analyze_question, validate_answer)
- **MCP Resources**: 2 (rag://documents, rag://stats)
- **Default Weights**: 60% vector + 40% graph

## Troubleshooting

### "No module named 'networkx'"
```bash
pip install networkx==3.1
```

### "No module named 'mcp'"
```bash
pip install mcp
```

### Graph has 0 nodes
- The document might be too short
- Try with a longer document (>500 words)
- Check that entities are being extracted

### MCP not showing
- Refresh the page (Ctrl+F5)
- Check server logs for errors
- Verify MCP client is initialized in views.py

## Next Steps

1. **Test with your own documents** - Upload PDFs about your domain
2. **Adjust weights** - Try different vector/graph ratios
3. **Add more relationship types** - Edit `rag/retrieval/graph.py`
4. **Visualize the graph** - Add D3.js or Cytoscape.js
5. **Add external MCP servers** - Web search, databases, APIs

## Support

- Read `UPGRADE_SUMMARY.md` for technical details
- Read `README.md` for complete documentation
- Check server logs for debugging
- Run `test_graph_mcp.py` to verify installation

---

**Your project is now a true "Agentic Graph-RAG 3.0 with MCP"! 🎉**

**Server running at: http://127.0.0.1:8000/**
