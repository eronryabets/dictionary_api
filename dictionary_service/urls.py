from django.urls import path, include
from rest_framework import routers
from .views import DictionaryViewSet, WordViewSet, TagViewSet

router = routers.DefaultRouter()
router.register(r'dictionaries', DictionaryViewSet, basename='dictionary')
router.register(r'words', WordViewSet, basename='word')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]
