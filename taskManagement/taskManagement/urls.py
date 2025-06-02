"""
URL configuration for taskManagement project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from tasks import views  # Import the views from tasks app
from django.contrib.auth import views as auth_views

# Swagger documentation
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Task Management API",
        default_version='v1',
        description="API for Task Management application",
        terms_of_service="https://www.taskmanagement.com/terms/",
        contact=openapi.Contact(email="contact@taskmanagement.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('tasks.urls')),
    path('api-auth/', include('rest_framework.urls')),
    
    # Swagger documentation with custom template
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', TemplateView.as_view(template_name='swagger/index.html'), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Frontend template URLs
    path('projects/', views.project_list_view, name='project-list'),
    path('projects/<int:pk>/', views.project_detail_view, name='project-detail'),
    path('projects/<int:pk>/edit/', views.project_update_view, name='project-update'),
    path('projects/<int:pk>/delete/', views.project_delete_view, name='project-delete'),
    path('projects/<int:pk>/add-member/', views.project_add_member_view, name='project-add-member'),
    
    path('tasks/<int:pk>/', views.task_detail_view, name='task-detail'),
    path('tasks/<int:pk>/edit/', views.task_update_view, name='task-update'),
    path('tasks/<int:pk>/delete/', views.task_delete_view, name='task-delete'),
    path('tasks/<int:pk>/add-comment/', views.task_add_comment_view, name='task-add-comment'),
    
    # User authentication views
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('profile/', views.profile_view, name='user-profile'),
    
    path('user/task-summary/', views.user_tasks_view, name='user-task-summary'),
    path('projects/<int:project_id>/metrics/', TemplateView.as_view(template_name='analytics/project_metrics.html'), name='project-metrics'),
    
    # New URL for creating task lists (redirects to project detail after creation)
    path('tasklists/create/', RedirectView.as_view(url='/projects/', permanent=False), name='tasklist-create'),
    
    # Redirect root URL to projects list instead of swagger docs
    path('', RedirectView.as_view(url='/projects/', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
