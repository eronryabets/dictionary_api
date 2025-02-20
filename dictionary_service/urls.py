from django.urls import path, include
from rest_framework import routers
from .views import DictionaryViewSet, WordViewSet, TagViewSet, BulkWordActionView, BulkDictionaryProgressView

router = routers.DefaultRouter()
router.register(r'dictionaries', DictionaryViewSet, basename='dictionary')
router.register(r'words', WordViewSet, basename='word')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('words/bulk_action/', BulkWordActionView.as_view(), name='bulk_action'),
    path('dictionary_progress/bulk/', BulkDictionaryProgressView.as_view(), name='bulk_dictionary_progress'),
    path('', include(router.urls)),
]
