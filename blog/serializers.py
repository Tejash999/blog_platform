from rest_framework import serializers
from .models import User, Profile, Post, Comment, Category, Tag


#Category Serializer
class CategorySerializer(serializers.ModelSerializer):
    
    # Serializer for the Category model. It converts Category objects to/from JSON.Used when listing or creating categories.
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

#Tag Serializer 
class TagSerializer(serializers.ModelSerializer):
    
    # Serializer for the Tag model. It converts Tag objects to/from JSON. It is used when listing or creating tags.
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


#Profile Serializer
class ProfileSerializer(serializers.ModelSerializer):
    # Serializer for the Profile model. It allows readers and authors to view and update their profile info.
    
    class Meta:
        model = Profile
        fields = ['id', 'bio', 'avatar', 'updated_at']
        read_only_fields = ['updated_at']


# User Serializer
class UserSerializer(serializers.ModelSerializer):

    # Serializer for the User model. It is used for displaying user info in posts and comments. Password is write-only so it never appears in API responses.

    profile = ProfileSerializer(read_only=True) # Nested serializer to include profile info when showing user data.

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'profile']
        read_only_fields = ['role']


#Register Serializer 
class RegisterSerializer(serializers.ModelSerializer): #Serializer for user registration. Accepts username, email, password, and role.
    
    # Hashes the password before saving using Django's set_password().
    # Also automatically creates a Profile for the new user.

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role']

    def create(self, validated_data):
        # Override create to hash the password properly.
        # Also creates an empty Profile linked to the new user.
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'reader'),
        )
        # Automatically create a profile for every new user
        Profile.objects.create(user=user)
        return user


# Comment Serializer
class CommentSerializer(serializers.ModelSerializer):
    # Serializer for the Comment model.
    # - 'author' is read-only and shows the username automatically.
    # - 'replies' is a nested list of child comments (threaded comments).
    # - 'parent' is optional — only set when replying to another comment.

    author = serializers.StringRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'parent', 'body', 'created_at', 'replies']
        read_only_fields = ['author', 'created_at']

    def get_replies(self, obj): #fetches all replies to this comment. Only top-level comments will have replies listed here.
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []


# Post List Serializer
class PostListSerializer(serializers.ModelSerializer): #serializer for listing many posts at once. It is used in the post list endpoint (GET /api/posts/).
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

    def get_comment_count(self, obj): # new method to count comments for each post 
        return obj.comments.count()


# Post Detail Serializer
class PostDetailSerializer(serializers.ModelSerializer):
    # Full serializer for a single post includes all fields. It is used in retrieve, create, and update endpoints.
    # category_id and tag_ids allow writing by ID.
    # category and tags fields show full nested data when reading.

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
        # Returns only top-level comments (no parent). Replies are nested inside each comment via CommentSerializer.
        top_level = obj.comments.filter(parent=None)
        return CommentSerializer(top_level, many=True).data 

#Login Serializer 
class LoginSerializer(serializers.Serializer): #accepts username and password for login and valid credentials.
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data): # check if suername and password are correct. 
        from django.contrib.auth import authenticate
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been disabled.")
        data['user'] = user
        return data


# Change password Serializer 
class ChangePasswordSerializer(serializers.Serializer): #serializer for changing password. requires old password to verify and confirm the new one
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data): # check if new_password and confirm-password match  
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords do not match.")
        return data

    def validate_old_password(self, value): # check that the old password is correct for the current user
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
        