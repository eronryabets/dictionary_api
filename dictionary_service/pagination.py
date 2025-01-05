from rest_framework.pagination import PageNumberPagination


class DictionaryPagination(PageNumberPagination):
    """
    Пагинация для списка словарей (Dictionary).

    - **page_size**: По умолчанию отображает 6 словарей на странице.
    - **page_size_query_param**: Позволяет клиенту задавать размер страницы через параметр запроса `page_size`.
    - **max_page_size**: Максимальное количество словарей на одной странице — 100.
    """
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 100


class WordPagination(PageNumberPagination):
    """
    Пагинация для списка слов (Word).

    - **page_size**: По умолчанию отображает 50 слов на странице.
    - **page_size_query_param**: Позволяет клиенту задавать размер страницы через параметр запроса `page_size`.
    - **max_page_size**: Максимальное количество слов на одной странице — 1000.
    """
    page_size = 50
    page_size_query_param = 'page_size'     # Позволяет клиенту задавать размер страницы через параметр запроса
    max_page_size = 1000
