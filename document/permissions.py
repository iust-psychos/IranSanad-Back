from rest_framework.permissions import BasePermission
from .models import Document, AccessLevel
from django.contrib.auth import get_user_model

User = get_user_model()

class HasAccessPermission(BasePermission):
    PERMISSION_MAP = {
        "Owner": 4,
        "Admin": 3,
        "Writer": 2,
        "ReadOnly": 1,
        "Deny": 0,
    }

    def __init__(self, required_level):
        self.required_level = required_level

    def _check_access(self, user, document_id):
        try:
            document_instance = Document.objects.get(pk=document_id)
        except Document.DoesNotExist:
            return False

        # try:
        #    user_instance = User.objects.get(pk=user.pk)
        # except User.DoesNotExist:
        #    return False
        user_instance = user

        if user_instance == document_instance.owner:
            AccessLevel.objects.update_or_create(
                user=user_instance,
                document=document_instance,
                defaults={"access_level": self.PERMISSION_MAP["Owner"]},
            )
            return True

        try:
            access_level = AccessLevel.objects.get(
                user=user_instance, document=document_instance
            )
            return access_level.access_level >= self.required_level
        except AccessLevel.DoesNotExist:
            default_access = document_instance.default_access_level
            AccessLevel.objects.create(
                user=user_instance,
                document=document_instance,
                access_level=default_access,
            )
            return default_access >= self.required_level

    def has_permission(self, request, view):
        document = view.kwargs.get("document") or request.data.get("document")
        if not document:
            return False
        return self._check_access(request.user, document)

    def has_object_permission(self, request, view, obj):
        document = obj.document if hasattr(obj, "document") else obj
        return self._check_access(request.user, document)


# Convenience permission classes for each level
class IsDocumentOwner(HasAccessPermission):
    def __init__(self):
        super().__init__(required_level=HasAccessPermission.PERMISSION_MAP["Owner"])


class IsDocumentAdmin(HasAccessPermission):
    def __init__(self):
        super().__init__(required_level=HasAccessPermission.PERMISSION_MAP["Admin"])


class IsDocumentWriter(HasAccessPermission):
    def __init__(self):
        super().__init__(required_level=HasAccessPermission.PERMISSION_MAP["Writer"])


class IsDocumentReadOnly(HasAccessPermission):
    def __init__(self):
        super().__init__(required_level=HasAccessPermission.PERMISSION_MAP["ReadOnly"])
