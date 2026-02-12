from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.home, name='home'),
    path('recent/', views.recent, name='recent'),
    path('search/', views.search, name='search'),
    path('category/<slug:slug>/', views.category_detail, name='category'),
    path('item/<int:pk>/', views.item_detail, name='item_detail'),
    # API
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/files/', views.api_files, name='api_files'),
]
