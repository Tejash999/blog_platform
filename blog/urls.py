from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, LogoutView,
    ChangePasswordView, UserDetailView,
    ProfileView, PostViewSet, CommentViewSet,
    CategoryViewSet, TagViewSet
)

# ─── ROUTER ───────────────────────────────────────────────────
# Automatically generates CRUD URLs for all ViewSets
router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    # Authentication endpoints 
    # POST /api/register/          (for creating new account)
    path('register/', RegisterView.as_view(), name='register'),

    # POST /api/login/             (to get JWT tokens)
    path('login/', LoginView.as_view(), name='login'),

    # POST /api/logout/            (blacklist refresh token for logging out)
    path('logout/', LogoutView.as_view(), name='logout'),

    # POST /api/change-password/   (change own password)
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),



    # User endpoints
    # GET/PUT /api/me/             (to view or update own account)
    path('me/', UserDetailView.as_view(), name='user_detail'),

    # GET/PUT /api/profile/        (to view or update own profile)
    path('profile/', ProfileView.as_view(), name='profile'),

    #Resource endpoints
    path('', include(router.urls)),
]