# urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'tasklists', views.TaskListViewSet, basename='tasklist')
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'comments', views.CommentViewSet, basename='comment')
router.register(r'attachments', views.TaskAttachmentViewSet, basename='attachment')

urlpatterns = [
    # API routes
    path('', include(router.urls)),
    
    # User management API endpoints
    path('register/', views.UserRegisterView.as_view(), name='api-register'),
    path('profile/', views.UserProfileView.as_view(), name='api-user-profile'),
    
    # Analytics API endpoints
    path('projects/<int:project_id>/metrics/', views.project_metrics, name='api-project-metrics'),
    path('user/task-summary/', views.user_task_summary, name='api-user-task-summary'),
    
    # JWT Authentication endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Template view handlers
    path('projects/list/', views.project_list_view, name='project-list-create'),
    path('projects/<int:pk>/view/', views.project_detail_view, name='project-view'),
    path('projects/<int:pk>/update/', views.project_update_view, name='project-update-handler'),
    path('projects/<int:pk>/delete/', views.project_delete_view, name='project-delete-handler'),
    path('projects/<int:pk>/add-member/', views.project_add_member_view, name='project-add-member-handler'),
    
    path('tasklists/create/', views.tasklist_create_view, name='tasklist-create-handler'),
    
    path('tasks/<int:pk>/view/', views.task_detail_view, name='task-view'),
    path('tasks/<int:pk>/update/', views.task_update_view, name='task-update-handler'),
    path('tasks/<int:pk>/delete/', views.task_delete_view, name='task-delete-handler'),
    path('tasks/<int:pk>/add-comment/', views.task_add_comment_view, name='task-add-comment-handler'),
    
    # User frontend view handlers
    path('user/register/', views.register_view, name='register-handler'),
    path('user/profile/', views.profile_view, name='user-profile-handler'),
    path('user/tasks/', views.user_tasks_view, name='user-task-summary-handler'),
]