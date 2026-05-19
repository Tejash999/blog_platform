from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, ProfileView,
    PostViewSet, CommentViewSet,
    CategoryViewSet, TagViewSet
)

# ─── ROUTER ───────────────────────────────────────────────────
# Automatically generates URL patterns for all ViewSets
# e.g. /api/posts/, /api/posts/{id}/, /api/comments/, etc.
router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    # User registration endpoint
    path('register/', RegisterView.as_view(), name='register'),

    # User profile endpoint (view and update own profile)
    path('profile/', ProfileView.as_view(), name='profile'),

    # All router-generated endpoints
    path('', include(router.urls)),
]