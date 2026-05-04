"""
Graph-based retrieval using NetworkX
Extracts entities and relationships to build a knowledge graph
"""
import networkx as nx
import pickle
import re
from pathlib import Path
from typing import List, Dict, Tuple, Set
from django.conf import settings
from collections import defaultdict


class GraphRetriever:
    """Build and query knowledge graphs from documents"""
    
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.graph = nx.DiGraph()
        self.graph_path = Path(settings.MEDIA_ROOT) / f"graph_{document_id}.pkl"
        self.entity_index = defaultdict(list)  # entity -> chunk_indices
    
    def extract_entities(self, text: str) -> Set[str]:
        """
        Extract entities (nouns, proper nouns, key terms)
        Simple rule-based extraction for educational purposes
        """
        # Capitalized words (likely proper nouns)
        proper_nouns = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text))
        
        # Technical terms (words with specific patterns)
        technical_terms = set(re.findall(r'\b(?:RAG|FAISS|LLM|API|MCP|Django|Python|AI|ML)\b', text))
        
        # Important keywords (3+ chars, appears multiple times)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = defaultdict(int)
        for word in words:
            word_freq[word] += 1
        
        frequent_words = {w for w, count in word_freq.items() if count >= 2}
        
        # Combine all entities
        entities = proper_nouns | technical_terms | frequent_words
        
        # Filter out common words
        stop_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'has'}
        entities = {e for e in entities if e.lower() not in stop_words}
        
        return entities
    
    def extract_relationships(self, text: str, entities: Set[str]) -> List[Tuple[str, str, str]]:
        """
        Extract relationships between entities
        Returns: [(entity1, relation, entity2), ...]
        """
        relationships = []
        
        # Common relationship patterns
        patterns = [
            (r'(\w+)\s+is\s+(?:a|an)\s+(\w+)', 'IS_A'),
            (r'(\w+)\s+uses\s+(\w+)', 'USES'),
            (r'(\w+)\s+includes\s+(\w+)', 'INCLUDES'),
            (r'(\w+)\s+requires\s+(\w+)', 'REQUIRES'),
            (r'(\w+)\s+implements\s+(\w+)', 'IMPLEMENTS'),
            (r'(\w+)\s+based\s+on\s+(\w+)', 'BASED_ON'),
        ]
        
        for pattern, relation_type in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity1, entity2 = match.groups()
                if entity1 in entities and entity2 in entities:
                    relationships.append((entity1, relation_type, entity2))
        
        # Co-occurrence relationships (entities in same sentence)
        sentences = re.split(r'[.!?]', text)
        for sentence in sentences:
            sentence_entities = [e for e in entities if e in sentence]
            if len(sentence_entities) >= 2:
                # Create co-occurrence edges
                for i, e1 in enumerate(sentence_entities):
                    for e2 in sentence_entities[i+1:]:
                        relationships.append((e1, 'CO_OCCURS', e2))
        
        return relationships
    
    def build_graph(self, chunks: List[str]) -> None:
        """
        Build knowledge graph from document chunks
        """
        self.graph.clear()
        self.entity_index.clear()
        
        for chunk_idx, chunk in enumerate(chunks):
            # Extract entities
            entities = self.extract_entities(chunk)
            
            # Add entities as nodes
            for entity in entities:
                if not self.graph.has_node(entity):
                    self.graph.add_node(entity, type='entity', frequency=1)
                else:
                    self.graph.nodes[entity]['frequency'] += 1
                
                # Index entity -> chunk mapping
                self.entity_index[entity].append(chunk_idx)
            
            # Extract and add relationships
            relationships = self.extract_relationships(chunk, entities)
            for e1, relation, e2 in relationships:
                if self.graph.has_edge(e1, e2):
                    self.graph[e1][e2]['weight'] += 1
                else:
                    self.graph.add_edge(e1, e2, relation=relation, weight=1)
        
        # Save graph
        with open(self.graph_path, 'wb') as f:
            pickle.dump({
                'graph': self.graph,
                'entity_index': dict(self.entity_index)
            }, f)
    
    def load_graph(self) -> bool:
        """Load existing graph"""
        if self.graph_path.exists():
            with open(self.graph_path, 'rb') as f:
                data = pickle.load(f)
                self.graph = data['graph']
                self.entity_index = defaultdict(list, data['entity_index'])
            return True
        return False
    
    def search_graph(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search graph for relevant entities and return associated chunks
        """
        if not self.load_graph():
            return []
        
        # Extract query entities
        query_entities = self.extract_entities(query)
        
        if not query_entities:
            return []
        
        # Find relevant entities using graph traversal
        relevant_entities = set()
        entity_scores = defaultdict(float)
        
        for query_entity in query_entities:
            # Direct match
            if query_entity in self.graph:
                relevant_entities.add(query_entity)
                entity_scores[query_entity] += self.graph.nodes[query_entity].get('frequency', 1)
                
                # Get neighbors (1-hop)
                neighbors = list(self.graph.neighbors(query_entity))
                for neighbor in neighbors[:5]:  # Limit to top 5 neighbors
                    relevant_entities.add(neighbor)
                    edge_weight = self.graph[query_entity][neighbor].get('weight', 1)
                    entity_scores[neighbor] += edge_weight * 0.5
        
        # Get chunks associated with relevant entities
        chunk_scores = defaultdict(float)
        for entity in relevant_entities:
            score = entity_scores[entity]
            for chunk_idx in self.entity_index.get(entity, []):
                chunk_scores[chunk_idx] += score
        
        # Sort and return top-k chunks
        sorted_chunks = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for chunk_idx, score in sorted_chunks:
            results.append({
                'chunk_index': chunk_idx,
                'score': float(score),
                'method': 'graph'
            })
        
        return results
    
    def get_graph_stats(self) -> Dict:
        """Get graph statistics"""
        if not self.graph:
            self.load_graph()
        
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'avg_degree': sum(dict(self.graph.degree()).values()) / max(self.graph.number_of_nodes(), 1)
        }
