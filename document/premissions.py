from rest_framework.permissions import BasePermission
from .models import *
class HasAccessPermission(BasePermission):
    def __init__(self, required_level):
        self.required_level = required_level
    
    def has_permission(self, request, view):
        # This will be checked at the view level
        document = view.kwargs.get('document') or request.data.get('document')
        if not document:
            return False
            
        try:
            access_level = AccessLevel.objects.get(
                user=request.user,
                document = document
            )
            return access_level.access_level >= self.required_level
        except AccessLevel.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        # This will be checked at the object level
        if hasattr(obj, 'document'):
            document = obj.document
        else:
            document = obj
            
        try:
            access_level = AccessLevel.objects.get(
                user=request.user,
                document=document
            )
            return access_level.access_level <= self.required_level
        except AccessLevel.DoesNotExist:
            return False

# Convenience permission classes for each level
class IsDocumentOwner(HasAccessPermission):
    def __init__(self):
        super().__init__(required_level=1)

class IsDocumentAdmin(HasAccessPermission):
    def __init__(self):
        super().__init__(required_level=2)

class IsDocumentWriter(HasAccessPermission):
    def __init__(self):
        super().__init__(required_level=3)

class IsDocumentReadOnly(HasAccessPermission):
    def __init__(self):
        super().__init__(required_level=4)