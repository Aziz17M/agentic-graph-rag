"""
Agent Executor: Récupère les chunks pertinents via Hybrid Retrieval
Uses MCP protocol for tool calls
"""
from typing import List, Dict
from rag.retrieval.hybrid import HybridRetriever
from rag.mcp.client import MCPClient


class ExecutorAgent:
    """Lance la recherche hybride (vector + graph) et récupère les chunks"""
    
    def __init__(self, document_id: str, use_mcp: bool = True):
        self.document_id = document_id
        self.retriever = HybridRetriever(document_id)
        self.use_mcp = use_mcp
        self.mcp_client = MCPClient() if use_mcp else None
    
    def retrieve(self, question: str, keywords: List[str], 
                 top_k: int = 3, method: str = 'hybrid') -> Dict:
        """
        Récupère les chunks les plus pertinents
        
        Args:
            question: Question to search
            keywords: Extracted keywords from Planner
            top_k: Number of results
            method: 'hybrid', 'vector', or 'graph'
        """
        # Load chunks for hybrid retriever
        from rag.models import Chunk
        chunks = Chunk.objects.filter(
            document_id=self.document_id
        ).order_by('chunk_index')
        self.retriever.chunks = [c.content for c in chunks]
        
        if self.use_mcp and self.mcp_client:
            # Use MCP protocol for retrieval
            tool_name = f"search_{method}"
            arguments = {
                "query": question,
                "document_id": self.document_id,
                "top_k": top_k
            }
            
            if method == 'hybrid':
                arguments["vector_weight"] = 0.6
                arguments["graph_weight"] = 0.4
            
            mcp_response = self.mcp_client.call_tool(
                tool_name=tool_name,
                arguments=arguments,
                context={
                    "keywords": keywords,
                    "agent": "executor"
                }
            )
            
            if "result" in mcp_response:
                results = mcp_response["result"]["content"]
            else:
                results = []
            
            return {
                'chunks': results,
                'count': len(results),
                'avg_score': sum(r['score'] for r in results) / len(results) if results else 0.0,
                'method': method,
                'mcp_call_id': mcp_response.get('id'),
                'mcp_used': True
            }
        else:
            # Direct retrieval without MCP
            if method == 'hybrid':
                results = self.retriever.search(question, top_k=top_k)
            elif method == 'vector':
                results = self.retriever.vector_retriever.search(question, top_k=top_k)
            elif method == 'graph':
                graph_results = self.retriever.graph_retriever.search_graph(question, top_k=top_k)
                # Convert graph results to standard format
                results = []
                for r in graph_results:
                    idx = r['chunk_index']
                    if idx < len(self.retriever.chunks):
                        results.append({
                            'content': self.retriever.chunks[idx],
                            'score': r['score'],
                            'index': idx,
                            'method': 'graph'
                        })
            else:
                results = self.retriever.search(question, top_k=top_k)
            
            return {
                'chunks': results,
                'count': len(results),
                'avg_score': sum(r['score'] for r in results) / len(results) if results else 0.0,
                'method': method,
                'mcp_used': False
            }
