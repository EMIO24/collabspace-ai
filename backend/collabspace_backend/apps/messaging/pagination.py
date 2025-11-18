from rest_framework.pagination import CursorPagination

class MessageCursorPagination(CursorPagination):
    """
    Cursor-based pagination for messages. 
    This is best for chat history as it ensures a stable ordering 
    and fast lookups for infinite scrolling.
    """
    page_size = 50
    ordering = '-created_at' # Newest messages first
    cursor_query_param = 'cursor'
    page_size_query_param = 'page_size'