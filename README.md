# 🤖 Agentic Graph-RAG 3.0

## 📋 Projet Universitaire - Tunis

Système de Question-Réponse Intelligent avec Architecture Multi-Agents

---

## 🎯 Objectif du Projet

Construire une application web qui permet à un utilisateur de :
1. **Importer** un document texte ou PDF
2. **Poser** une question en langage naturel
3. **Recevoir** une réponse générée par un LLM local, basée uniquement sur le contenu du document, avec sources citées et score de confiance

---

## �️ Concepts Implémentés

### 1. RAG (Retrieval-Augmented Generation)
Le système ne répond pas de mémoire. Il recherche d'abord les passages pertinents dans le document, puis les injecte dans le prompt du LLM pour générer une réponse fondée sur des sources réelles.

### 2. Vector Retrieval avec FAISS
Les documents sont découpés en chunks de 500 mots, encodés en vecteurs (384 dimensions) avec sentence-transformers (modèle all-MiniLM-L6-v2), et indexés dans FAISS. La recherche se fait par similarité cosinus.

### 3. Architecture Agentic : Planner / Executor / Critic
Trois agents travaillent en séquence :
- **Planner** : Analyse la question, identifie les mots-clés, reformule si nécessaire
- **Executor** : Lance la recherche FAISS et récupère les 3 chunks les plus pertinents
- **Critic** : Vérifie que la réponse générée est cohérente avec les sources trouvées

### 4. MCP (Model Context Protocol)
Chaque appel entre agents suit un Tool Schema MCP standardisé avec : nom de l'outil, paramètres typés, contexte injecté (chunks, scores, trace_id), et annotations (readOnly, verifiable). Cela rend chaque étape traçable et auditable.

### 5. LLM Local avec Ollama
Le LLM utilisé est llama3.2:1b, tournant en local via Ollama. Aucune clé API externe n'est nécessaire.

---

## 🚀 Installation et Démarrage

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

## 📊 Pipeline Complet

```
[Document] → [Découpage chunks] → [Encodage vectoriel] → [Indexation FAISS]
                                                                ↓
[Question] → [Planner] → [Executor] → [LLM Ollama] → [Critic] → [Réponse]
               ↓            ↓                           ↓
             MCP          MCP                         MCP
               ↓            ↓                           ↓
                    [Base de données SQLite]
```

### Détails du Pipeline

1. **Indexation** (5-10 secondes)
   - Extraction du texte (PyPDF2)
   - Découpage en chunks de 500 mots
   - Encodage en vecteurs (sentence-transformers)
   - Indexation FAISS (similarité cosinus)

2. **Question-Réponse** (3-7 secondes)
   - **Planner** : Analyse la question, extrait mots-clés (~50ms)
   - **Executor** : Recherche FAISS top-3 chunks (~100ms)
   - **LLM** : Génère réponse basée sur les chunks (2-5s)
   - **Critic** : Valide cohérence et calcule score de confiance (~50ms)

---

## 🎬 Utilisation

### 1. Importer un Document
- Cliquer sur "Sélectionner un fichier"
- Choisir un PDF ou TXT
- Cliquer sur "Indexer le document"
- Attendre 5-10 secondes

### 2. Poser une Question
- Sélectionner le document (cliquez dessus, il devient bleu)
- Taper votre question
- Cliquer sur "Lancer le pipeline RAG"
- Attendre 3-7 secondes

### 3. Résultat
Vous obtenez :
- ✅ Réponse générée avec sources citées
- 🎯 Score de confiance (0-100%)
- ✅ Validation du Critic (validé/non validé)
- � 3 sources avec leurs scores de similarité
- 🆔 Trace ID unique pour traçabilité

---

## 🧪 Tests

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
python test_system.py
```
Vérifie : Planner, Executor, Critic, FAISS, MCP, Ollama, Base de données

---

## 🔧 Technologies

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Backend | Django 4.2 | Framework web |
| Base de données | SQLite | Stockage (Document, Chunk, QueryLog) |
| Embeddings | sentence-transformers | Encodage vectoriel (all-MiniLM-L6-v2) |
| Recherche | FAISS | Similarité cosinus |
| LLM | Ollama (llama3.2:1b) | Génération de réponses |
| Frontend | HTML/CSS/JS | Interface utilisateur |
| Protocol | MCP | Traçabilité inter-agents |

---

## 📁 Structure du Projet

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
│   │   ├── executor.py # Recherche FAISS
│   │   └── critic.py   # Validation cohérence
│   │
│   ├── retrieval/      # Recherche Vectorielle
│   │   └── vector.py   # FAISS + embeddings
│   │
│   ├── mcp/            # Model Context Protocol
│   │   └── tools.py    # MCPToolSchema
│   │
│   └── llm/            # LLM Local
│       └── ollama.py   # Client Ollama
│
├── templates/
│   └── demo.html       # Interface unique
│
├── media/              # Documents + index FAISS
├── test_document.txt   # Document de test
├── test_system.py      # Tests automatiques
├── test_top_k.py       # Test différentes valeurs top-k
├── requirements.txt    # Dépendances
└── README.md           # Ce fichier
```

---

## ⚙️ Configuration

### Pourquoi top-3 chunks ?
Le système récupère les **3 chunks les plus pertinents** car :
- Équilibre optimal entre contexte et bruit
- Recherche scientifique : c'est le sweet spot prouvé
- Limites du LLM : llama3.2:1b gère bien 3 chunks
- Performance : Rapide et efficace

**C'est configurable !** Dans `rag/agents/executor.py` :
```python
def retrieve(self, question: str, keywords: List[str], top_k: int = 3):
    #                                                              ↑
    #                                                    Changez ici (1-10)
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

## 🆘 Problèmes Courants

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

---

## 📊 Performances

| Opération | Temps |
|-----------|-------|
| Indexation (10 pages) | 5-10s |
| Recherche FAISS | <50ms |
| Génération LLM | 2-5s |
| Pipeline complet | 3-7s |

---

## 🎓 Équipe

Projet universitaire réalisé par 5 étudiants à Tunis

---

## 📝 Licence

Projet universitaire - Usage éducatif uniquement

---

## 🎯 Points Forts

1. ✅ **Minimaliste** : 6 dépendances seulement
2. ✅ **Fonctionnel** : Système complet et opérationnel
3. ✅ **Pédagogique** : Code clair et bien documenté
4. ✅ **Démontrable** : Interface web intuitive
5. ✅ **Traçable** : MCP pour auditabilité complète
6. ✅ **Local** : Pas de dépendance externe (Ollama)
7. ✅ **Extensible** : Architecture modulaire

---

**Le système est prêt. Bonne présentation ! 🚀**
