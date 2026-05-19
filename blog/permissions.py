from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission for blog posts.
    - Anyone can read (GET, HEAD, OPTIONS).
    - Only users with role='author' can create posts.
    - Only the post owner can edit or delete their own post.
    """

    def has_permission(self, request, view):
        """
        Allow read-only access to everyone.
        Only allow write access to authenticated authors.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'author'

    def has_object_permission(self, request, view, obj):
        """
        Allow read access to everyone.
        Only allow edit/delete to the post's own author.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission for comments and profiles.
    - Anyone can read.
    - Only the owner of the object can edit or delete it.
    """

    def has_permission(self, request, view):
        """
        Allow read-only to everyone.
        Require authentication for write operations.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Allow read access to everyone.
        Only allow edit/delete to the object's author.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user