# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file),
    path('preview/<int:file_id>/', views.preview_file),
    path('process/<int:file_id>/', views.process_file),
]