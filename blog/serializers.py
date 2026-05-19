from rest_framework import serializers
from .models import User, Profile, Post, Comment, Category, Tag


#Category Serializer
class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model.
    Converts Category objects to/from JSON.
    Used when listing or creating categories.
    """

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


#Tag Serializer 
class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for the Tag model.
    Converts Tag objects to/from JSON.
    Used when listing or creating tags.
    """

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


#Profile Serializer
class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the Profile model.
    Allows readers and authors to view and update their profile info.
    """

    class Meta:
        model = Profile
        fields = ['id', 'bio', 'avatar', 'updated_at']
        read_only_fields = ['updated_at']


# ─── USER SERIALIZER ──────────────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    Used for displaying user info in posts and comments.
    Includes nested profile data.
    Password is write-only so it never appears in API responses.
    """

    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'profile']
        read_only_fields = ['role']


# ─── REGISTER SERIALIZER ──────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Accepts username, email, password, and role.
    Hashes the password before saving using Django's set_password().
    Also automatically creates a Profile for the new user.
    """

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role']

    def create(self, validated_data):
        """
        Override create to hash the password properly.
        Also creates an empty Profile linked to the new user.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'reader'),
        )
        # Automatically create a profile for every new user
        Profile.objects.create(user=user)
        return user


# ─── COMMENT SERIALIZER ───────────────────────────────────────
class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Comment model.
    - 'author' is read-only and shows the username automatically.
    - 'replies' is a nested list of child comments (threaded comments).
    - 'parent' is optional — only set when replying to another comment.
    """

    author = serializers.StringRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'parent', 'body', 'created_at', 'replies']
        read_only_fields = ['author', 'created_at']

    def get_replies(self, obj):
        """
        Recursively fetches all replies to this comment.
        Only top-level comments will have replies listed here.
        """
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []


# ─── POST LIST SERIALIZER ─────────────────────────────────────
class PostListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing many posts at once.
    Shows only summary fields — no full content.
    Used in the post list endpoint (GET /api/posts/).
    """

    author = serializers.StringRelatedField(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'author', 'category',
            'tags', 'status', 'published_at', 'created_at', 'comment_count'
        ]

    def get_comment_count(self, obj):
        """
        Returns the total number of comments on this post.
        Shown in the list view so users know how active a post is.
        """
        return obj.comments.count()


# ─── POST DETAIL SERIALIZER ───────────────────────────────────
class PostDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for a single post — includes all fields.
    Used in retrieve, create, and update endpoints.
    - category_id and tag_ids allow writing by ID.
    - category and tags fields show full nested data when reading.
    """

    author = serializers.StringRelatedField(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()

    # Write-only fields for setting category and tags by ID
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source='tags',
        write_only=True,
        many=True,
        required=False
    )

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'author', 'category', 'category_id',
            'tags', 'tag_ids', 'content', 'status', 'published_at',
            'created_at', 'updated_at', 'comments'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']

    def get_comments(self, obj):
        """
        Returns only top-level comments (no parent).
        Replies are nested inside each comment via CommentSerializer.
        """
        top_level = obj.comments.filter(parent=None)
        return CommentSerializer(top_level, many=True).data