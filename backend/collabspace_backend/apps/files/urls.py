from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

app_name = 'files'

router = DefaultRouter()
router.register('', FileViewSet, basename='file')

urlpatterns = [
    # DRF ViewSet URLs
    path('', include(router.urls)),
    
    # Custom URLs
    path('shared/<str:token>/', SharedFileView.as_view(), name='shared-file'),
    path('storage-stats/', FileStorageStatsView.as_view(), name='storage-stats'),
]