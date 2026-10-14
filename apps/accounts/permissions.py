from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    message = "Your role does not allow this action"

    def has_permission(self, request, view):
        # 1. Anonymous users are denied.
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. Missing configuration must deny access.
        allowed_roles = getattr(view, "allowed_roles", None)

        if allowed_roles is None:
            return False

        # 3. Only explicitly allowed roles may proceed.
        return getattr(request.user, "role", None) in allowed_roles
