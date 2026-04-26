"""
MCP (Model Context Protocol) Tool Schema
Standardise les appels entre agents avec traçabilité
"""
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
import uuid

@dataclass
class MCPToolSchema:
    """Schéma standardisé pour chaque appel d'agent"""
    tool_name: str
    parameters: Dict[str, Any]
    context: Dict[str, Any]
    trace_id: str
    annotations: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.annotations is None:
            self.annotations = {"readOnly": False, "verifiable": True}
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class MCPTools:
    """Outils MCP pour la communication inter-agents"""
    
    @staticmethod
    def create_planner_call(question: str, trace_id: str = None) -> MCPToolSchema:
        """Crée un appel MCP pour le Planner"""
        return MCPToolSchema(
            tool_name="planner.analyze_question",
            parameters={"question": question},
            context={"agent": "planner", "step": 1},
            trace_id=trace_id or str(uuid.uuid4()),
            annotations={"readOnly": True, "verifiable": True}
        )
    
    @staticmethod
    def create_executor_call(keywords: List[str], question: str, trace_id: str) -> MCPToolSchema:
        """Crée un appel MCP pour l'Executor"""
        return MCPToolSchema(
            tool_name="executor.retrieve_chunks",
            parameters={"keywords": keywords, "question": question, "top_k": 3},
            context={"agent": "executor", "step": 2},
            trace_id=trace_id,
            annotations={"readOnly": True, "verifiable": True}
        )
    
    @staticmethod
    def create_critic_call(answer: str, chunks: List[Dict], trace_id: str) -> MCPToolSchema:
        """Crée un appel MCP pour le Critic"""
        return MCPToolSchema(
            tool_name="critic.validate_answer",
            parameters={"answer": answer, "source_chunks": chunks},
            context={"agent": "critic", "step": 3},
            trace_id=trace_id,
            annotations={"readOnly": True, "verifiable": True}
        )
