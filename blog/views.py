from rest_framework import viewsets, generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.contrib.auth import authenticate

from .models import User, Profile, Post, Comment, Category, Tag
from .serializers import (
    UserSerializer, RegisterSerializer, ProfileSerializer,
    PostListSerializer, PostDetailSerializer,
    CommentSerializer, CategorySerializer, TagSerializer,
    LoginSerializer, ChangePasswordSerializer
)
from .permissions import IsAuthorOrReadOnly, IsOwnerOrReadOnly
from .filters import PostFilter, CommentFilter
from .pagination import StandardPagination, CommentPagination


#Register View 
class RegisterView(generics.CreateAPIView):
    
    # This is public endpoint for user registration. Anyone can POST to this to create a new account. Returns the created user data on success.
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


#Profile View 
class ProfileView(generics.RetrieveUpdateAPIView):
    
    # This class only allows authenticated users to view and update their own profile.
    # GET /api/profile/ returns the current user's profile
    # PUT /api/profile/ updates bio or avatar
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Returns the profile belonging to the currently logged-in user.
        No need to pass a profile ID — it's tied to the request user.
        """
        return self.request.user.profile


#Category ViewSet
class CategoryViewSet(viewsets.ModelViewSet):

    # Full CRUD for blog categories: Anyone can view categories (GET) and Only authenticated users can create, update, or delete.
    # Supports searching by name 
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'slug']


# Tag Viewset
class TagViewSet(viewsets.ModelViewSet):
    # Full CRUD for blog tags.
    # Anyone can view tags (GET) and Only authenticated users can create, update, or delete.
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'slug']


# post viewset 
class PostViewSet(viewsets.ModelViewSet):
    # Full CRUD for blog posts with search, filtering, and pagination.
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PostFilter
    search_fields = ['title', 'content', 'author__username', 'category__name']
    ordering_fields = ['created_at', 'published_at', 'title']
    ordering = ['-created_at']

    def get_serializer_class(self):
        
        # Using lightweight serializer for list view and full serializer for detail, create, and update views.
        if self.action == 'list':
            return PostListSerializer
        return PostDetailSerializer

    def get_queryset(self):
        # Authenticated authors can see their own draft posts. Everyone else only sees published posts.
        user = self.request.user
        if user.is_authenticated and user.role == 'author':
            return Post.objects.filter(author=user)
        return Post.objects.filter(status='published')

    def perform_create(self, serializer):
        # Automatically set the logged-in user as the post author.Sets published_at if the post is being published immediately.
        status_value = serializer.validated_data.get('status', 'draft')
        published_at = timezone.now() if status_value == 'published' else None
        serializer.save(author=self.request.user, published_at=published_at)

    def perform_update(self, serializer):
        # When updating a post, set published_at if status changes to published.
        status_value = serializer.validated_data.get('status', 'draft')
        published_at = timezone.now() if status_value == 'published' else None
        serializer.save(published_at=published_at)


#Comment ViewSet
class CommentViewSet(viewsets.ModelViewSet):

    # Full CRUD for comments with filtering and pagination. only authenticated users can create comments. 
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrReadOnly]
    pagination_class = CommentPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = CommentFilter
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def perform_create(self, serializer):
        """
        Automatically set the logged-in user as the comment author.
        """
        serializer.save(author=self.request.user)

# Login View 
class LoginView(APIView): #Custom login endpoint which accepts username and password. also return jwt access along with user info 

    permission_classes = [permissions.AllowAny]
    def post(self, request): # Validate credentials and return JWT tokens. The access token is used for API requests.The refresh token is used to get a new access token.
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generate JWT tokens for the user
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            return Response({
                'message': 'Login successful.',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                },
                'tokens': {
                    'access': str(access),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Logout View
class LogoutView(APIView):# Logout endpoint. Blacklists the refresh token so it can no longer be used. The user must send their refresh token in the request body.
   

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request): #Accept the refresh token and blacklist it. This effectively logs the user out by invalidating their token.

        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {'message': 'Logout successful.'},
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception:
            return Response(
                {'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


# Change password View 
class ChangePasswordView(APIView): #Allows authenticated users to change their password.It requires old password for verification.It requires new password and confirmation to match.
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request): # It validates old password, then set new password.It returns success message on completion.
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            # Set the new password and save
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response(
                {'message': 'Password changed successfully.'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#User detail view 
class UserDetailView(generics.RetrieveUpdateAPIView): # alllows unauntheticated users to view and update their account 
   
    # GET  /api/me/ → returns current user info
    # PUT  /api/me/ → updates username or email

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self): #returns currently logged-in user 
        return self.request.user