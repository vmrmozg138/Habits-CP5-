from rest_framework.pagination import PageNumberPagination

class HabitPageNumberPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    page_query_param = 'page'
    max_page_size = 10