from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for most API endpoints.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class SmallResultsSetPagination(PageNumberPagination):
    """
    Pagination for endpoints that should return fewer results.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination for endpoints that need to return more results.
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
