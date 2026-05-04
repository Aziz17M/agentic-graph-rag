# Agentic Graph-RAG 3.0

## Projet Universitaire - Tunis

Système de Question-Réponse Intelligent avec Architecture Multi-Agents, Graph Retrieval et MCP Protocol

---

## Objectif du Projet

Construire une application web qui permet à un utilisateur de :
1. **Importer** un document texte ou PDF
2. **Poser** une question en langage naturel
3. **Recevoir** une réponse générée par un LLM local, basée sur une recherche hybride (Vector + Graph), avec sources citées et score de confiance

---

## Concepts Implémentés

### 1. RAG (Retrieval-Augmented Generation)
Le système ne répond pas de mémoire. Il recherche d'abord les passages pertinents dans le document, puis les injecte dans le prompt du LLM pour générer une réponse fondée sur des sources réelles.

### 2. Graph Retrieval (Knowledge Graph)
Les documents sont analysés pour extraire des entités (noms propres, termes techniques) et leurs relations (IS_A, USES, INCLUDES, REQUIRES, IMPLEMENTS, BASED_ON, CO_OCCURS). Un graphe de connaissances est construit avec NetworkX pour permettre une recherche par traversée de graphe.

### 3. Hybrid Retrieval (Vector + Graph)
Combine deux méthodes de recherche :
- **Vector Search (FAISS)**: Similarité cosinus sur embeddings (60% du score)
- **Graph Search (NetworkX)**: Traversée de graphe avec expansion 1-hop (40% du score)

### 4. Architecture Agentic : Planner / Executor / Critic
Trois agents travaillent en séquence via MCP :
- **Planner** : Analyse la question, identifie les mots-clés, reformule si nécessaire
- **Executor** : Lance la recherche hybride (vector + graph) et récupère les chunks
- **Critic** : Vérifie que la réponse générée est cohérente avec les sources trouvées

### 5. MCP (Model Context Protocol)
Implémentation complète du protocole MCP (JSON-RPC 2.0) :
- **5 outils MCP** : search_vector, search_graph, search_hybrid, analyze_question, validate_answer
- **2 ressources MCP** : rag://documents, rag://stats
- **Session management** : Traçabilité complète avec session_id et call history
- **Interoperability** : Communication standardisée entre agents

### 6. LLM Local avec Ollama
Le LLM utilisé est llama3.2:1b, tournant en local via Ollama. Aucune clé API externe n'est nécessaire.

---

## Installation et Démarrage

### Prérequis
- Python 3.10+
- Ollama avec llama3.2:1b

### Installation

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Créer la base de données
python manage.py migrate

# 3. Vérifier qu'Ollama est installé
ollama list
# Si llama3.2:1b n'est pas présent:
ollama pull llama3.2:1b

# 4. Lancer le serveur
python manage.py runserver
```

### Accès
Ouvrir le navigateur : **http://127.0.0.1:8000/**

---

## Pipeline Complet

```
[Document] → [Découpage chunks] → [Encodage vectoriel] → [Indexation FAISS]
                                                                ↓
                                                    [Construction du graphe]
                                                    ├─ Extraction entités
                                                    └─ Détection relations
                                                                ↓
[Question] → [MCP: Planner] → [MCP: Executor] → [LLM Ollama] → [MCP: Critic] → [Réponse]
                  ↓                  ↓                              ↓
              Keywords      Hybrid Retrieval                   Validation
                            (Vector + Graph)
```

### Détails du Pipeline

1. **Indexation** (5-15 secondes)
   - Extraction du texte (PyPDF2)
   - Découpage en chunks de 500 mots
   - Encodage en vecteurs (sentence-transformers)
   - Indexation FAISS (similarité cosinus)
   - Construction du graphe de connaissances (NetworkX)

2. **Question-Réponse** (3-7 secondes)
   - **Planner** (via MCP): Analyse la question, extrait mots-clés (~50ms)
   - **Executor** (via MCP): Recherche hybride (vector + graph) top-3 chunks (~150ms)
   - **LLM**: Génère réponse basée sur les chunks (2-5s)
   - **Critic** (via MCP): Valide cohérence et calcule score de confiance (~50ms)

---

## Utilisation

### 1. Importer un Document
- Cliquer sur "Sélectionner un fichier"
- Choisir un PDF ou TXT
- Cliquer sur "Indexer le document"
- Attendre 5-15 secondes (indexation vector + graph)

### 2. Poser une Question
- Sélectionner le document (cliquez dessus, il devient bleu)
- Taper votre question
- Cliquer sur "Lancer le pipeline RAG"
- Attendre 3-7 secondes

### 3. Résultat
Vous obtenez :
- Réponse générée avec sources citées
- Score de confiance (0-100%)
- Validation du Critic (validé/non validé)
- 3 sources avec leurs scores (hybrid, vector, graph)
- Méthode de retrieval utilisée (hybrid/vector/graph)
- MCP session ID pour traçabilité
- Trace ID unique

---

## Tests

### Document de Test
Un fichier `test_document.txt` est fourni avec le projet (contenu sur l'IA et le RAG).

### Questions de Test

**Question pertinente :**
```
"Qu'est-ce que le RAG ?"
→ Score attendu : 75-95%
→ Réponse détaillée avec sources
```

**Question hors contexte :**
```
"Quelle est la capitale de la France ?"
→ Score attendu : 10-30%
→ Le système indique qu'il ne trouve pas l'info
```

### Tests Automatiques
```bash
# Tests système complets
python test_system.py

# Tests Graph + MCP
python test_graph_mcp.py
```

---

## Technologies

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Backend | Django 4.2 | Framework web |
| Base de données | SQLite | Stockage (Document, Chunk, QueryLog) |
| Embeddings | sentence-transformers | Encodage vectoriel (all-MiniLM-L6-v2) |
| Vector Search | FAISS | Similarité cosinus |
| Graph | NetworkX 3.1 | Graphe de connaissances |
| Protocol | MCP 1.27+ | Model Context Protocol (JSON-RPC 2.0) |
| LLM | Ollama (llama3.2:1b) | Génération de réponses |
| Frontend | HTML/CSS/JS | Interface utilisateur |

---

## Structure du Projet

```
agentic_rag/
├── config/              # Configuration Django
│   ├── settings.py     # SQLite, Ollama config
│   ├── urls.py
│   └── wsgi.py
│
├── rag/                 # Application principale
│   ├── models.py       # Document, Chunk, QueryLog
│   ├── views.py        # upload_document, ask_question
│   ├── urls.py
│   ├── admin.py
│   │
│   ├── agents/         # Architecture Multi-Agents
│   │   ├── planner.py  # Analyse et reformulation
│   │   ├── executor.py # Recherche hybride (vector + graph)
│   │   └── critic.py   # Validation cohérence
│   │
│   ├── retrieval/      # Recherche Hybride
│   │   ├── vector.py   # FAISS + embeddings
│   │   ├── graph.py    # Knowledge graph (NetworkX)
│   │   └── hybrid.py   # Combinaison vector + graph
│   │
│   ├── mcp/            # Model Context Protocol
│   │   ├── server.py   # MCP Server (tools + resources)
│   │   ├── client.py   # MCP Client (JSON-RPC 2.0)
│   │   └── tools.py    # Legacy MCP schema
│   │
│   └── llm/            # LLM Local
│       └── ollama.py   # Client Ollama
│
├── templates/
│   └── demo.html       # Interface unique
│
├── media/              # Documents + index FAISS + graphes
├── test_document.txt   # Document de test
├── test_system.py      # Tests automatiques
├── test_graph_mcp.py   # Tests Graph + MCP
├── requirements.txt    # Dépendances
├── README.md           # Ce fichier
└── UPGRADE_SUMMARY.md  # Détails de l'upgrade Graph-RAG + MCP
```

---

## Configuration

### Pourquoi Hybrid Retrieval (60% Vector + 40% Graph) ?
- **Vector (60%)**: Excellente pour la similarité sémantique
- **Graph (40%)**: Capture les relations et le contexte structurel
- **Combinaison**: Meilleur des deux mondes

**C'est configurable !** Dans `rag/agents/executor.py` :
```python
def retrieve(self, question: str, keywords: List[str], 
             top_k: int = 3, method: str = 'hybrid'):
    # method: 'hybrid', 'vector', or 'graph'
    # Pour hybrid, ajustez les poids:
    vector_weight=0.6, graph_weight=0.4
```

### Variables d'Environnement
Fichier `.env` :
```env
DEBUG=True
SECRET_KEY=django-insecure-dev-key-change-in-production
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
```

---

## MCP Protocol Details

### MCP Tools Available
1. **search_vector**: Recherche par similarité vectorielle (FAISS)
2. **search_graph**: Recherche par traversée de graphe (NetworkX)
3. **search_hybrid**: Recherche hybride (vector + graph)
4. **analyze_question**: Analyse de question (Planner)
5. **validate_answer**: Validation de réponse (Critic)

### MCP Resources Available
1. **rag://documents**: Liste des documents indexés
2. **rag://stats**: Statistiques du système

### MCP Call Example
```python
from rag.mcp.client import MCPClient

client = MCPClient("rag-server")
response = client.call_tool(
    tool_name="search_hybrid",
    arguments={
        "query": "What is RAG?",
        "document_id": "doc-123",
        "top_k": 3,
        "vector_weight": 0.6,
        "graph_weight": 0.4
    },
    context={"trace_id": "abc-123"}
)
```

---

## Problèmes Courants

### Le serveur ne démarre pas
```bash
python manage.py migrate
python manage.py runserver
```

### Ollama ne répond pas
```bash
ollama serve
ollama list
ollama pull llama3.2:1b
```

### Erreur lors de l'upload
- Vérifier que le dossier `media/` existe
- Vider le cache du navigateur (Ctrl+F5)
- Vérifier les logs du serveur

### Score de confiance toujours faible
- Reformuler la question plus clairement
- Vérifier que le document est bien indexé
- Tester avec le document de test fourni
- Vérifier que le graphe a été construit (voir graph_nodes > 0)

---

## Performances

| Opération | Temps |
|-----------|-------|
| Indexation vector (10 pages) | 5-10s |
| Construction graphe (10 pages) | 2-5s |
| Recherche FAISS | <50ms |
| Recherche graphe | <100ms |
| Recherche hybride | <150ms |
| Génération LLM | 2-5s |
| Pipeline complet | 3-7s |

---

## Équipe

Projet universitaire réalisé par 5 étudiants à Tunis

---

## Licence

Projet universitaire - Usage éducatif uniquement

---

## Points Forts

1. **Graph-RAG**: Extraction automatique d'entités et relations
2. **Hybrid Retrieval**: Combine vector similarity et graph traversal
3. **Real MCP Protocol**: JSON-RPC 2.0 avec tools et resources
4. **Interoperability**: Communication standardisée entre agents
5. **Provenance Tracing**: trace_id + MCP session + call history
6. **Dynamic Tool Selection**: Choix vector/graph/hybrid via MCP
7. **Minimaliste**: Code clair et bien documenté
8. **Fonctionnel**: Système complet et opérationnel
9. **Démontrable**: Interface web intuitive
10. **Local**: Pas de dépendance externe (Ollama)

---

## Coverage des Requirements

| Requirement | Status | Implementation |
|------------|--------|----------------|
| Interoperability (MCP) | ✅ DONE | Real MCP protocol (JSON-RPC 2.0) |
| Agent-based reasoning | ✅ DONE | Planner, Executor, Critic via MCP |
| Hybrid retrieval | ✅ DONE | Vector (FAISS) + Graph (NetworkX) |
| Verifiable answers | ✅ DONE | Full provenance (trace_id + MCP session) |
| Dynamic context injection | ✅ DONE | MCP tools with context parameters |
| Graph retrieval | ✅ DONE | Entity extraction + relationship detection |
| Dynamic tool usage | ✅ DONE | MCP tool selection (vector/graph/hybrid) |

---

**Le système est prêt. Bonne présentation ! 🚀**

**Voir UPGRADE_SUMMARY.md pour les détails techniques de l'upgrade.**
