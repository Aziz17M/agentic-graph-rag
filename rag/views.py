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
            retriever = VectorRetriever(str(doc.id))
            chunks = retriever.create_chunks(text, chunk_size=500)
            
            # Sauvegarde des chunks en DB
            for i, chunk_text in enumerate(chunks):
                Chunk.objects.create(
                    document=doc,
                    content=chunk_text,
                    chunk_index=i
                )
            
            # Indexation FAISS
            retriever.index_chunks(chunks)
            doc.indexed = True
            doc.save()
            
            return JsonResponse({
                'success': True,
                'document_id': str(doc.id),
                'title': doc.title,
                'chunks_count': len(chunks)
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
            
            # Étape 1: Planner
            planner = PlannerAgent()
            mcp_planner = MCPTools.create_planner_call(question, trace_id)
            plan_result = planner.analyze(question)
            
            # Étape 2: Executor
            executor = ExecutorAgent(document_id)
            mcp_executor = MCPTools.create_executor_call(
                plan_result['keywords'], 
                question, 
                trace_id
            )
            exec_result = executor.retrieve(question, plan_result['keywords'])
            
            # Étape 3: LLM Generation
            ollama = OllamaClient()
            answer = ollama.generate_with_chunks(question, exec_result['chunks'])
            
            # Étape 4: Critic
            critic = CriticAgent()
            mcp_critic = MCPTools.create_critic_call(answer, exec_result['chunks'], trace_id)
            validation = critic.validate(answer, exec_result['chunks'])
            
            # Sauvegarde du log
            query_log = QueryLog.objects.create(
                trace_id=trace_id,
                document=doc,
                question=question,
                reformulated_question=plan_result['reformulated'],
                retrieved_chunks=[{
                    'content': c['content'][:200] + '...',
                    'score': c['score']
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
                'reformulated': plan_result['reformulated']
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
