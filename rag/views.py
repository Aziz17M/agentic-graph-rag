from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import PyPDF2
import uuid
import os

from .models import Document, Chunk, QueryLog
from .retrieval.vector import VectorRetriever
from .agents.planner import PlannerAgent
from .agents.executor import ExecutorAgent
from .agents.critic import CriticAgent
from .llm.ollama import OllamaClient
from .mcp.tools import MCPTools

def index(request):
    """Page principale"""
    documents = Document.objects.all().order_by('-uploaded_at')
    return render(request, 'demo.html', {'documents': documents})

@csrf_exempt
def upload_document(request):
    """Upload et indexation d'un document"""
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            file = request.FILES['document']
            title = request.POST.get('title', file.name)
            
            # Sauvegarde du document
            doc = Document.objects.create(title=title, file_path=file)
            
            # Extraction du texte
            text = extract_text(doc.file_path.path)
            
            # Découpage en chunks
            from rag.retrieval.hybrid import HybridRetriever
            retriever = HybridRetriever(str(doc.id))
            from rag.retrieval.vector import VectorRetriever
            vector_ret = VectorRetriever(str(doc.id))
            chunks = vector_ret.create_chunks(text, chunk_size=500)
            
            # Sauvegarde des chunks en DB
            for i, chunk_text in enumerate(chunks):
                Chunk.objects.create(
                    document=doc,
                    content=chunk_text,
                    chunk_index=i
                )
            
            # Indexation Hybrid (Vector + Graph)
            retriever.index_document(chunks)
            doc.indexed = True
            doc.save()
            
            # Get graph stats
            graph_stats = retriever.graph_retriever.get_graph_stats()
            
            return JsonResponse({
                'success': True,
                'document_id': str(doc.id),
                'title': doc.title,
                'chunks_count': len(chunks),
                'graph_nodes': graph_stats['nodes'],
                'graph_edges': graph_stats['edges']
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de l\'indexation: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Fichier manquant'}, status=400)

@csrf_exempt
def ask_question(request):
    """Pipeline complet de question-réponse"""
    if request.method == 'POST':
        try:
            document_id = request.POST.get('document_id')
            question = request.POST.get('question')
            
            if not document_id or not question:
                return JsonResponse({
                    'success': False,
                    'error': 'Paramètres manquants'
                }, status=400)
            
            doc = get_object_or_404(Document, id=document_id)
            trace_id = str(uuid.uuid4())
            
            # Initialize MCP Client
            from rag.mcp.client import MCPClient
            mcp_client = MCPClient()
            
            # Étape 1: Planner (via MCP)
            mcp_planner_response = mcp_client.call_tool(
                tool_name="analyze_question",
                arguments={"question": question},
                context={"trace_id": trace_id, "step": 1}
            )
            plan_result = mcp_planner_response["result"]["content"]
            
            # Étape 2: Executor (Hybrid Retrieval via MCP)
            executor = ExecutorAgent(document_id, use_mcp=True)
            exec_result = executor.retrieve(
                question, 
                plan_result['keywords'],
                method='hybrid'  # Use hybrid retrieval
            )
            
            # Étape 3: LLM Generation
            ollama = OllamaClient()
            answer = ollama.generate_with_chunks(question, exec_result['chunks'])
            
            # Étape 4: Critic (via MCP)
            mcp_critic_response = mcp_client.call_tool(
                tool_name="validate_answer",
                arguments={
                    "answer": answer,
                    "chunks": exec_result['chunks']
                },
                context={"trace_id": trace_id, "step": 3}
            )
            validation = mcp_critic_response["result"]["content"]
            
            # Sauvegarde du log
            query_log = QueryLog.objects.create(
                trace_id=trace_id,
                document=doc,
                question=question,
                reformulated_question=plan_result['reformulated'],
                retrieved_chunks=[{
                    'content': c['content'][:200] + '...',
                    'score': c['score'],
                    'vector_score': c.get('vector_score', 0),
                    'graph_score': c.get('graph_score', 0),
                    'method': c.get('method', 'hybrid')
                } for c in exec_result['chunks']],
                answer=answer,
                confidence_score=validation['confidence'],
                critic_validation=validation['is_valid']
            )
            
            return JsonResponse({
                'success': True,
                'trace_id': trace_id,
                'answer': answer,
                'confidence': validation['confidence'],
                'is_valid': validation['is_valid'],
                'chunks': exec_result['chunks'],
                'keywords': plan_result['keywords'],
                'reformulated': plan_result['reformulated'],
                'retrieval_method': exec_result['method'],
                'mcp_used': True,
                'mcp_session': mcp_client.get_session_info()
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors du traitement: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

def extract_text(file_path):
    """Extrait le texte d'un PDF ou TXT"""
    if file_path.endswith('.pdf'):
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ''
            for page in reader.pages:
                text += page.extract_text() + '\n'
        return text
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
