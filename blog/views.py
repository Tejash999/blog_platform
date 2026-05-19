from rest_framework import viewsets, generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import User, Profile, Post, Comment, Category, Tag
from .serializers import (
    UserSerializer, RegisterSerializer, ProfileSerializer,
    PostListSerializer, PostDetailSerializer,
    CommentSerializer, CategorySerializer, TagSerializer
)
from .permissions import IsAuthorOrReadOnly, IsOwnerOrReadOnly

# Create your views here.

# ─── REGISTER VIEW ────────────────────────────────────────────
class RegisterView(generics.CreateAPIView):
    """
    Public endpoint for user registration.
    Anyone can POST to this to create a new account.
    Returns the created user data on success.
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# ─── PROFILE VIEW ─────────────────────────────────────────────
class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Allows authenticated users to view and update their own profile.
    GET  /api/profile/ → returns the current user's profile
    PUT  /api/profile/ → updates bio or avatar
    """

    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Returns the profile belonging to the currently logged-in user.
        No need to pass a profile ID — it's tied to the request user.
        """
        return self.request.user.profile


# ─── CATEGORY VIEWSET ─────────────────────────────────────────
class CategoryViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for blog categories.
    - Anyone can view categories (GET).
    - Only admin users can create, update, or delete categories.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# ─── TAG VIEWSET ──────────────────────────────────────────────
class TagViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for blog tags.
    - Anyone can view tags (GET).
    - Only authenticated users can create, update, or delete tags.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# ─── POST VIEWSET ─────────────────────────────────────────────
class PostViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for blog posts.
    - Anyone can read published posts.
    - Only authors can create posts.
    - Only the post owner can update or delete their own post.

    Also supports:
    - Search by title, content, author username
    - Filter by category, tags, status, published_at
    - Ordering by created_at or published_at
    """

    queryset = Post.objects.filter(status='published')
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be filtered exactly
    filterset_fields = ['category', 'tags', 'status', 'author']

    # Fields that can be searched with ?search=
    search_fields = ['title', 'content', 'author__username']

    # Fields that can be ordered with ?ordering=
    ordering_fields = ['created_at', 'published_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """
        Use lightweight serializer for list view.
        Use full serializer for detail, create, and update views.
        """
        if self.action == 'list':
            return PostListSerializer
        return PostDetailSerializer

    def get_queryset(self):
        """
        Authenticated authors can also see their own draft posts.
        Everyone else only sees published posts.
        """
        user = self.request.user
        if user.is_authenticated and user.role == 'author':
            return Post.objects.filter(author=user)
        return Post.objects.filter(status='published')

    def perform_create(self, serializer):
        """
        Automatically set the logged-in user as the post author.
        Also sets published_at if the post status is 'published'.
        """
        status_value = serializer.validated_data.get('status', 'draft')
        published_at = timezone.now() if status_value == 'published' else None
        serializer.save(author=self.request.user, published_at=published_at)

    def perform_update(self, serializer):
        """
        When updating, set published_at if status changes to published.
        """
        status_value = serializer.validated_data.get('status', 'draft')
        published_at = timezone.now() if status_value == 'published' else None
        serializer.save(published_at=published_at)


# ─── COMMENT VIEWSET ──────────────────────────────────────────
class CommentViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for comments.
    - Anyone can read comments.
    - Authenticated users can create comments.
    - Only the comment owner can update or delete their comment.
    Supports pagination automatically via DRF settings.
    """

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post', 'author', 'parent']

    def perform_create(self, serializer):
        """
        Automatically set the logged-in user as the comment author.
        """
        serializer.save(author=self.request.user)

