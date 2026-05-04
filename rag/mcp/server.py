"""
Real MCP (Model Context Protocol) Server Implementation
Provides tools and resources via standardized protocol
"""
from mcp.server import Server
from mcp.types import Tool, TextContent, Resource
from typing import Any, Sequence
import json


class RAGMCPServer:
    """
    MCP Server for RAG operations
    Exposes tools for document retrieval and agent operations
    """
    
    def __init__(self):
        self.server = Server("rag-server")
        self.setup_tools()
        self.setup_resources()
    
    def setup_tools(self):
        """Register MCP tools"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="search_vector",
                    description="Search documents using vector similarity (FAISS)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "document_id": {
                                "type": "string",
                                "description": "Document ID to search"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results",
                                "default": 3
                            }
                        },
                        "required": ["query", "document_id"]
                    }
                ),
                Tool(
                    name="search_graph",
                    description="Search documents using knowledge graph traversal",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "document_id": {
                                "type": "string",
                                "description": "Document ID to search"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results",
                                "default": 3
                            }
                        },
                        "required": ["query", "document_id"]
                    }
                ),
                Tool(
                    name="search_hybrid",
                    description="Search using hybrid retrieval (vector + graph)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "document_id": {
                                "type": "string",
                                "description": "Document ID to search"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results",
                                "default": 3
                            },
                            "vector_weight": {
                                "type": "number",
                                "description": "Weight for vector similarity (0-1)",
                                "default": 0.6
                            },
                            "graph_weight": {
                                "type": "number",
                                "description": "Weight for graph relevance (0-1)",
                                "default": 0.4
                            }
                        },
                        "required": ["query", "document_id"]
                    }
                ),
                Tool(
                    name="analyze_question",
                    description="Analyze question and extract keywords (Planner agent)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "Question to analyze"
                            }
                        },
                        "required": ["question"]
                    }
                ),
                Tool(
                    name="validate_answer",
                    description="Validate answer coherence with sources (Critic agent)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "answer": {
                                "type": "string",
                                "description": "Generated answer"
                            },
                            "chunks": {
                                "type": "array",
                                "description": "Source chunks",
                                "items": {"type": "object"}
                            }
                        },
                        "required": ["answer", "chunks"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
            """Execute tool calls"""
            
            if name == "search_vector":
                from rag.retrieval.vector import VectorRetriever
                retriever = VectorRetriever(arguments["document_id"])
                results = retriever.search(
                    arguments["query"], 
                    top_k=arguments.get("top_k", 3)
                )
                return [TextContent(
                    type="text",
                    text=json.dumps(results, indent=2)
                )]
            
            elif name == "search_graph":
                from rag.retrieval.graph import GraphRetriever
                retriever = GraphRetriever(arguments["document_id"])
                results = retriever.search_graph(
                    arguments["query"],
                    top_k=arguments.get("top_k", 3)
                )
                return [TextContent(
                    type="text",
                    text=json.dumps(results, indent=2)
                )]
            
            elif name == "search_hybrid":
                from rag.retrieval.hybrid import HybridRetriever
                retriever = HybridRetriever(arguments["document_id"])
                results = retriever.search(
                    arguments["query"],
                    top_k=arguments.get("top_k", 3),
                    vector_weight=arguments.get("vector_weight", 0.6),
                    graph_weight=arguments.get("graph_weight", 0.4)
                )
                return [TextContent(
                    type="text",
                    text=json.dumps(results, indent=2)
                )]
            
            elif name == "analyze_question":
                from rag.agents.planner import PlannerAgent
                planner = PlannerAgent()
                result = planner.analyze(arguments["question"])
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            
            elif name == "validate_answer":
                from rag.agents.critic import CriticAgent
                critic = CriticAgent()
                result = critic.validate(
                    arguments["answer"],
                    arguments["chunks"]
                )
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    def setup_resources(self):
        """Register MCP resources"""
        
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """List available resources"""
            return [
                Resource(
                    uri="rag://documents",
                    name="Documents",
                    description="List of indexed documents",
                    mimeType="application/json"
                ),
                Resource(
                    uri="rag://stats",
                    name="System Statistics",
                    description="RAG system statistics",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content"""
            
            if uri == "rag://documents":
                from rag.models import Document
                docs = Document.objects.all().values('id', 'title', 'indexed', 'uploaded_at')
                return json.dumps(list(docs), default=str, indent=2)
            
            elif uri == "rag://stats":
                from rag.models import Document, Chunk, QueryLog
                stats = {
                    'documents': Document.objects.count(),
                    'chunks': Chunk.objects.count(),
                    'queries': QueryLog.objects.count()
                }
                return json.dumps(stats, indent=2)
            
            else:
                raise ValueError(f"Unknown resource: {uri}")
    
    def get_server(self) -> Server:
        """Get the MCP server instance"""
        return self.server


# Global MCP server instance
mcp_server = RAGMCPServer()
