from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

class AgencyManagerRequiredMixin(AccessMixin):
    """Verify that the current user is an agency manager."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.groups.filter(name='Agency Managers').exists():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

class AgencyStaffRequiredMixin(AccessMixin):
    """Verify that the current user is an agency staff member."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.groups.filter(name='Agency Staff').exists():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)