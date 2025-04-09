from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at', 'updated_at')
    search_fields = ('title', 'owner__username')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner')
    
    def owner(self, obj):
        return obj.owner.username if obj.owner else 'Unknown'
    