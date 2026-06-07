from rest_framework import viewsets, generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.contrib.auth import authenticate

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

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
@extend_schema(   # Decorator for RegisterView 
    tags=['Authentication'],
    summary='Register a new user',
    description='Creates a new user account. Role can be author or reader. A profile is automatically created.',
)
class RegisterView(generics.CreateAPIView):
    
    # This is public endpoint for user registration. Anyone can POST to this to create a new account. Returns the created user data on success.
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


#Profile View 
@extend_schema( # Decorator for ProfileView
    tags=['User'],
    summary='Get or update current user profile',
    description='Returns the profile of the currently logged in user. Allows updating bio and avatar.',
)
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
@extend_schema_view( #Decorator for CategoryViewSet
    list=extend_schema(
        tags=['Categories'],
        summary='List all categories',
        description='Returns a list of all blog categories. Supports search by name.',
    ),
    retrieve=extend_schema(
        tags=['Categories'],
        summary='Get a single category',
    ),
    create=extend_schema(
        tags=['Categories'],
        summary='Create a new category',
        description='Creates a new category. Requires authentication.',
    ),
    update=extend_schema(tags=['Categories'], summary='Update a category'),
    partial_update=extend_schema(tags=['Categories'], summary='Partially update a category'),
    destroy=extend_schema(tags=['Categories'], summary='Delete a category'),
)
class CategoryViewSet(viewsets.ModelViewSet):

    # Full CRUD for blog categories: Anyone can view categories (GET) and Only authenticated users can create, update, or delete.
    # Supports searching by name 
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'slug']


# Tag Viewset
@extend_schema_view( # Decorator for TagViewSet
    list=extend_schema(
        tags=['Tags'],
        summary='List all tags',
        description='Returns a list of all blog tags. Supports search by name.',
    ),
    retrieve=extend_schema(tags=['Tags'], summary='Get a single tag'),
    create=extend_schema(tags=['Tags'], summary='Create a new tag'),
    update=extend_schema(tags=['Tags'], summary='Update a tag'),
    partial_update=extend_schema(tags=['Tags'], summary='Partially update a tag'),
    destroy=extend_schema(tags=['Tags'], summary='Delete a tag'),
)
class TagViewSet(viewsets.ModelViewSet):
    # Full CRUD for blog tags.
    # Anyone can view tags (GET) and Only authenticated users can create, update, or delete.
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'slug']


# post viewset 
@extend_schema_view(  # Decorator for PostViewSet
    list=extend_schema(
        tags=['Posts'],
        summary='List all published posts',
        description='''
            Returns a paginated list of published blog posts.
            
            It give the following Filtering options:
            - ?search=keyword        : search in title, content, author, category
            - ?category=1            : filter by category ID
            - ?tags=2                : filter by tag ID
            - ?author=john           : filter by author username
            - ?status=published      : filter by status
            - ?published_after=YYYY-MM-DD
            - ?published_before=YYYY-MM-DD
            - ?ordering=created_at   : sort results
            - ?page=2                : go to page 2
            - ?page_size=5           : items per page ''',
        parameters=[
            OpenApiParameter('search', OpenApiTypes.STR, description='Search in title, content, author'),
            OpenApiParameter('category', OpenApiTypes.INT, description='Filter by category ID'),
            OpenApiParameter('tags', OpenApiTypes.INT, description='Filter by tag ID'),
            OpenApiParameter('author', OpenApiTypes.STR, description='Filter by author username'),
            OpenApiParameter('status', OpenApiTypes.STR, description='Filter by status: draft or published'),
            OpenApiParameter('published_after', OpenApiTypes.DATE, description='Posts published after this date'),
            OpenApiParameter('published_before', OpenApiTypes.DATE, description='Posts published before this date'),
            OpenApiParameter('ordering', OpenApiTypes.STR, description='Order by: created_at, published_at, title'),
            OpenApiParameter('page', OpenApiTypes.INT, description='Page number'),
            OpenApiParameter('page_size', OpenApiTypes.INT, description='Number of results per page'),
        ]
    ),
    retrieve=extend_schema(
        tags=['Posts'],
        summary='Get a single post',
        description='Returns full details of a single post including all comments.',
    ),
    create=extend_schema(
        tags=['Posts'],
        summary='Create a new post',
        description='Creates a new blog post. Only users with role=author can create posts.',
    ),
    update=extend_schema(
        tags=['Posts'],
        summary='Update a post',
        description='Updates a post. Only the post author can update their own post.',
    ),
    partial_update=extend_schema(
        tags=['Posts'],
        summary='Partially update a post',
    ),
    destroy=extend_schema(
        tags=['Posts'],
        summary='Delete a post',
        description='Deletes a post. Only the post author can delete their own post.',
    ),
)
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
@extend_schema_view(   # Decorator for CommentViewSet
    list=extend_schema(
        tags=['Comments'],
        summary='List all comments',
        description='''
            Returns a paginated list of comments.
            Filtering options:
            - ?post=1        :all comments on a specific post
            - ?author=john   :all comments by a specific author
            - ?parent=5      :all replies to a specific comment
            - ?page=2        :go to page 2
            - ?page_size=10  :items per page ''',
        parameters=[
            OpenApiParameter('post', OpenApiTypes.INT, description='Filter by post ID'),
            OpenApiParameter('author', OpenApiTypes.STR, description='Filter by author username'),
            OpenApiParameter('parent', OpenApiTypes.INT, description='Filter replies by parent comment ID'),
        ]
    ),
    
    retrieve=extend_schema(tags=['Comments'], summary='Get a single comment'),
    create=extend_schema(
        tags=['Comments'],
        summary='Create a comment',
        description='Creates a new comment on a post. Set parent to reply to another comment.',
    ),
    
    update=extend_schema(tags=['Comments'], summary='Update a comment'),
    partial_update=extend_schema(tags=['Comments'], summary='Partially update a comment'),
    destroy=extend_schema(tags=['Comments'], summary='Delete a comment'),
)
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
@extend_schema(   # Decorator for LoginView 
    tags=['Authentication'],
    summary='Login and get JWT tokens',
    description='Accepts username and password. Returns access and refresh JWT tokens on success.',
)
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
@extend_schema(  # Decorator for LogoutView 
    tags=['Authentication'],
    summary='Logout and blacklist refresh token',
    description='Blacklists the refresh token so it can no longer be used to get new access tokens.',
)
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
@extend_schema( # Decorator for ChangePasswordView 
    tags=['Authentication'],
    summary='Change user password',
    description='Allows authenticated users to change their password by providing the old and new password.',
)
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
@extend_schema( #Decorator for UserDetailView 
    tags=['User'],
    summary='Get or update current user',
    description='Returns the currently logged in user info. Also allows updating username and email.',
)
class UserDetailView(generics.RetrieveUpdateAPIView): # alllows unauntheticated users to view and update their account 
   
    # GET  /api/me/ → returns current user info
    # PUT  /api/me/ → updates username or email

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self): #returns currently logged-in user 
        return self.request.user