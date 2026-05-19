from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


#Standard Pagination is used for listing blog posts 
class StandardPagination(PageNumberPagination):
 
    # Default page size is 10 items per page.
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

    def get_paginated_response(self, data):
        
        # Custom response format that includes:
        # count: total number of items
        # total_pages: how many pages exist
        # next: link to next page
        # previous: link to previous page
        # results: the actual data
        
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


#Comment pagination is used for listing comments under a post
class CommentPagination(PageNumberPagination):
    
    # Smaller page size since comments are shorter.
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Custom response format for comment threads.
        Same structure as StandardPagination for consistency.
        """
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })