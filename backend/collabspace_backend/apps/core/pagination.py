from typing import Any, Dict, Optional
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 200
    page_query_param = "page"


class SmallResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50
    page_query_param = "page"


class CustomPageNumberPagination(PageNumberPagination):
    """
    Returns a custom response format:
    {
        "status": "success",
        "message": "Items retrieved",
        "results": [...],
        "meta": {
            "count": 123,
            "next": "...",
            "previous": "...",
            "page": 2,
            "page_size": 50,
            "total_pages": 3
        }
    }
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200

    def get_paginated_response(self, data) -> Response:
        page_number = self.page.number if hasattr(self.page, "number") else None
        page_size = self.get_page_size(self.request)
        total_pages = self.page.paginator.num_pages if hasattr(self.page, "paginator") else None
        return Response(
            {
                "status": "success",
                "message": "OK",
                "results": data,
                "meta": {
                    "count": self.page.paginator.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "page": page_number,
                    "page_size": page_size,
                    "total_pages": total_pages,
                },
            }
        )


class LargeCursorPagination(CursorPagination):
    """
    Cursor-based pagination suitable for large, changing datasets.
    """
    page_size = 200
    ordering = "-created"  # default ordering field; override per-view if needed
    cursor_query_param = "cursor"
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_paginated_response(self, data) -> Response:
        return Response(
            {
                "status": "success",
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )
