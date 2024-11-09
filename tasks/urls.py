# urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'tasklists', views.TaskListViewSet, basename='tasklist')
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'comments', views.CommentViewSet, basename='comment')
router.register(r'attachments', views.TaskAttachmentViewSet, basename='attachment')

urlpatterns = [
    path('', include(router.urls)),
]