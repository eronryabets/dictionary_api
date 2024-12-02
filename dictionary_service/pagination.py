from rest_framework.pagination import PageNumberPagination


class DictionaryPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 100


class WordPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'     # Позволяет клиенту задавать размер страницы через параметр запроса
    max_page_size = 1000
