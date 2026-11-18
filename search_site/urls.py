from django.contrib import admin
from django.urls import URLPattern, URLResolver, path
from search_app import views

urlpatterns: list[URLPattern | URLResolver] = [
    path('admin/', admin.site.urls),
    path('', views.search_view, name='search'),
    path('api/search/', views.api_search, name='api_search'),
]

