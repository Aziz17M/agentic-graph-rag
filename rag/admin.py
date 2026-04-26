from django.contrib import admin
from .models import Document, Chunk, QueryLog

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'uploaded_at', 'indexed']
    list_filter = ['indexed', 'uploaded_at']

@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ['document', 'chunk_index', 'created_at']
    list_filter = ['document']

@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ['trace_id', 'document', 'question', 'confidence_score', 'created_at']
    list_filter = ['document', 'created_at']
