"""
MCP Client for interacting with RAG MCP Server
"""
from typing import Dict, Any, List
import uuid
import json
from datetime import datetime


class MCPClient:
    """
    Client for MCP protocol communication
    Handles tool calls and resource access
    """
    
    def __init__(self, server_name: str = "rag-server"):
        self.server_name = server_name
        self.session_id = str(uuid.uuid4())
        self.call_history = []
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any], 
                  context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call an MCP tool with proper protocol structure
        
        Returns MCP-compliant response with metadata
        """
        call_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Build MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": call_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Add context if provided
        if context:
            mcp_request["params"]["context"] = context
        
        # Execute tool (in real implementation, this would be async/network call)
        try:
            result = self._execute_tool(tool_name, arguments)
            
            # Build MCP response
            mcp_response = {
                "jsonrpc": "2.0",
                "id": call_id,
                "result": {
                    "content": result,
                    "isError": False
                },
                "meta": {
                    "server": self.server_name,
                    "session_id": self.session_id,
                    "timestamp": timestamp,
                    "tool": tool_name
                }
            }
            
        except Exception as e:
            # Error response
            mcp_response = {
                "jsonrpc": "2.0",
                "id": call_id,
                "error": {
                    "code": -32000,
                    "message": str(e)
                },
                "meta": {
                    "server": self.server_name,
                    "session_id": self.session_id,
                    "timestamp": timestamp,
                    "tool": tool_name
                }
            }
        
        # Log call
        self.call_history.append({
            "request": mcp_request,
            "response": mcp_response,
            "timestamp": timestamp
        })
        
        return mcp_response
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute the actual tool logic"""
        
        if tool_name == "search_vector":
            from rag.retrieval.vector import VectorRetriever
            retriever = VectorRetriever(arguments["document_id"])
            return retriever.search(
                arguments["query"],
                top_k=arguments.get("top_k", 3)
            )
        
        elif tool_name == "search_graph":
            from rag.retrieval.graph import GraphRetriever
            retriever = GraphRetriever(arguments["document_id"])
            results = retriever.search_graph(
                arguments["query"],
                top_k=arguments.get("top_k", 3)
            )
            # Load actual chunks
            from rag.models import Chunk
            chunks = Chunk.objects.filter(
                document_id=arguments["document_id"]
            ).order_by('chunk_index')
            chunk_list = list(chunks)
            
            formatted_results = []
            for result in results:
                idx = result['chunk_index']
                if idx < len(chunk_list):
                    formatted_results.append({
                        'content': chunk_list[idx].content,
                        'score': result['score'],
                        'index': idx,
                        'method': 'graph'
                    })
            return formatted_results
        
        elif tool_name == "search_hybrid":
            from rag.retrieval.hybrid import HybridRetriever
            retriever = HybridRetriever(arguments["document_id"])
            # Load chunks first
            from rag.models import Chunk
            chunks = Chunk.objects.filter(
                document_id=arguments["document_id"]
            ).order_by('chunk_index')
            retriever.chunks = [c.content for c in chunks]
            
            return retriever.search(
                arguments["query"],
                top_k=arguments.get("top_k", 3),
                vector_weight=arguments.get("vector_weight", 0.6),
                graph_weight=arguments.get("graph_weight", 0.4)
            )
        
        elif tool_name == "analyze_question":
            from rag.agents.planner import PlannerAgent
            planner = PlannerAgent()
            return planner.analyze(arguments["question"])
        
        elif tool_name == "validate_answer":
            from rag.agents.critic import CriticAgent
            critic = CriticAgent()
            return critic.validate(
                arguments["answer"],
                arguments["chunks"]
            )
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Read an MCP resource
        """
        request_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        mcp_request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "resources/read",
            "params": {
                "uri": uri
            }
        }
        
        try:
            content = self._read_resource(uri)
            
            mcp_response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(content, default=str, indent=2)
                        }
                    ]
                },
                "meta": {
                    "server": self.server_name,
                    "session_id": self.session_id,
                    "timestamp": timestamp
                }
            }
            
        except Exception as e:
            mcp_response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": str(e)
                }
            }
        
        return mcp_response
    
    def _read_resource(self, uri: str) -> Any:
        """Read resource content"""
        
        if uri == "rag://documents":
            from rag.models import Document
            docs = Document.objects.all().values('id', 'title', 'indexed', 'uploaded_at')
            return list(docs)
        
        elif uri == "rag://stats":
            from rag.models import Document, Chunk, QueryLog
            return {
                'documents': Document.objects.count(),
                'chunks': Chunk.objects.count(),
                'queries': QueryLog.objects.count()
            }
        
        else:
            raise ValueError(f"Unknown resource: {uri}")
    
    def get_call_history(self) -> List[Dict]:
        """Get history of all MCP calls"""
        return self.call_history
    
    def get_session_info(self) -> Dict:
        """Get current session information"""
        return {
            "session_id": self.session_id,
            "server": self.server_name,
            "total_calls": len(self.call_history)
        }
