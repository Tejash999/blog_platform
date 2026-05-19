import django_filters
from .models import Post, Comment


#Post Filter 
class PostFilter(django_filters.FilterSet):
   
    # Filter by partial title match 
    title = django_filters.CharFilter(
        field_name='title',
        lookup_expr='icontains',
        help_text="Search posts by partial title (case-insensitive)."
    )

    # Filter by author username author=john
    author = django_filters.CharFilter(
        field_name='author__username',
        lookup_expr='icontains',
        help_text="Filter posts by author username."
    )

    # Filter by category id category=1
    category = django_filters.NumberFilter(
        field_name='category__id',
        help_text="Filter posts by category ID."
    )

    # Filter by tag id  tags=2
    tags = django_filters.NumberFilter(
        field_name='tags__id',
        help_text="Filter posts by tag ID."
    )

    # Filter by status status=published
    status = django_filters.CharFilter(
        field_name='status',
        lookup_expr='exact',
        help_text="Filter by status: draft or published."
    )

    # Filter posts published after a date published_after=2024-01-01
    published_after = django_filters.DateFilter(
        field_name='published_at',
        lookup_expr='gte',
        help_text="Show posts published on or after this date (YYYY-MM-DD)."
    )

    # Filter posts published before a date published_before=2024-12-31
    published_before = django_filters.DateFilter(
        field_name='published_at',
        lookup_expr='lte',
        help_text="Show posts published on or before this date (YYYY-MM-DD)."
    )

    class Meta:
        model = Post
        fields = ['title', 'author', 'category', 'tags', 'status', 'published_after', 'published_before']


# ─── COMMENT FILTER ───────────────────────────────────────────
class CommentFilter(django_filters.FilterSet):
    """
    Custom filter class for comments.
    Allows filtering comments by:
    - post   → filter all comments belonging to a specific post
    - author → filter by author username
    """

    # Filter by post id — ?post=1
    post = django_filters.NumberFilter(
        field_name='post__id',
        help_text="Filter comments by post ID."
    )

    # Filter by author username — ?author=john
    author = django_filters.CharFilter(
        field_name='author__username',
        lookup_expr='icontains',
        help_text="Filter comments by author username."
    )

    class Meta:
        model = Comment
        fields = ['post', 'author']