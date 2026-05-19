from django.db import models
from django.contrib.auth.models import AbstractUser


# ─── USER MODEL ───────────────────────────────────────────────
class User(AbstractUser):
    
    # Custom user model extending Django's built-in AbstractUser.
    # Adds a 'role' field to distinguish between authors and readers.
    

    ROLE_CHOICES = [
        ('author', 'Author'),
        ('reader', 'Reader'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='reader',
        help_text="Defines what the user can do: authors manage posts, readers manage comments."
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


# ─── PROFILE MODEL ────────────────────────────────────────────
class Profile(models.Model):
    """
    One-to-one extension of the User model.
    Stores extra display information like bio and avatar.
    Created automatically when a new user registers.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(blank=True, null=True, help_text="Short description about the user.")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


# ─── CATEGORY MODEL ───────────────────────────────────────────
class Category(models.Model):
    """
    Represents a blog category (e.g. Technology, Travel).
    Each post belongs to exactly one category.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, help_text="URL-friendly version of the name.")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


# ─── TAG MODEL ────────────────────────────────────────────────
class Tag(models.Model):
    """
    Represents a tag that can be attached to many posts.
    Posts and tags have a many-to-many relationship.
    """

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.name


# ─── POST MODEL ───────────────────────────────────────────────
class Post(models.Model):
    """
    The main content model for blog posts.
    - An author (User with role='author') writes posts.
    - Each post belongs to one Category and can have many Tags.
    - Status field allows saving drafts before publishing.
    - slug is used for clean, human-readable URLs.
    """

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        limit_choices_to={'role': 'author'}
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='posts'
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft'
    )
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Newest posts appear first

    def __str__(self):
        return f"{self.title} [{self.status}]"


# ─── COMMENT MODEL ────────────────────────────────────────────
class Comment(models.Model):
    """
    Represents a comment on a blog post.
    - Supports threaded/nested comments via the 'parent' self-referential FK.
    - If parent is None, it is a top-level comment.
    - If parent has a value, it is a reply to that comment.
    """

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text="If this is a reply, point to the parent comment."
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']  # Oldest comments appear first

    def __str__(self):
        return f"Comment by {self.author.username} on '{self.post.title}'"


