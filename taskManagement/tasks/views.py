# views.py
from rest_framework import viewsets, permissions, filters, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Case, When, IntegerField, F, Avg
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Project, TaskList, Task, Comment, TaskAttachment
from .serializers import (
    ProjectSerializer, TaskListSerializer, TaskSerializer,
    CommentSerializer, TaskAttachmentSerializer, UserSerializer
)
from .forms import CustomUserCreationForm
from .filters import ProjectFilter, TaskListFilter, TaskFilter
from .permissions import (
    IsOwnerOrReadOnly, IsProjectOwnerOrMember, IsTaskListProjectOwnerOrMember,
    IsTaskProjectOwnerOrMember, IsCommentAuthorOrProjectMember, IsAttachmentUploaderOrProjectMember
)

# User Registration and Management Views
class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        form = CustomUserCreationForm(request.data)
        if form.is_valid():
            user = form.save()
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectFilter
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']

    def get_queryset(self):
        return Project.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).distinct()

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        project = self.get_object()
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            project.members.add(user)
            return Response({'status': 'member added'})
        except User.DoesNotExist:
            return Response({'error': 'user not found'}, status=404)

class TaskListViewSet(viewsets.ModelViewSet):
    serializer_class = TaskListSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskListProjectOwnerOrMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskListFilter
    search_fields = ['name']
    ordering_fields = ['position', 'created_at']

    def get_queryset(self):
        return TaskList.objects.filter(
            project__in=Project.objects.filter(
                Q(owner=self.request.user) | Q(members=self.request.user)
            )
        )

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskProjectOwnerOrMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'priority', 'status', 'position']

    def get_queryset(self):
        return Task.objects.filter(
            task_list__project__in=Project.objects.filter(
                Q(owner=self.request.user) | Q(members=self.request.user)
            )
        )

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        task = self.get_object()
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            task.assigned_to = user
            task.save()
            return Response({'status': 'task assigned'})
        except User.DoesNotExist:
            return Response({'error': 'user not found'}, status=404)

    @action(detail=True, methods=['post'])
    def update_position(self, request, pk=None):
        task = self.get_object()
        new_position = request.data.get('position')
        task.position = new_position
        task.save()
        return Response({'status': 'position updated'})
    
    @action(detail=True, methods=['post'])
    def add_dependency(self, request, pk=None):
        """Add a dependency to this task"""
        task = self.get_object()
        dependency_id = request.data.get('dependency_id')
        
        if not dependency_id:
            return Response({'error': 'dependency_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            dependency = Task.objects.get(id=dependency_id)
            
            # Check for circular dependencies
            if dependency.id == task.id:
                return Response(
                    {'error': 'Task cannot depend on itself'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if dependency.dependencies.filter(id=task.id).exists():
                return Response(
                    {'error': 'This would create a circular dependency'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if this dependency is already added
            if task.dependencies.filter(id=dependency.id).exists():
                return Response({'status': 'dependency already exists'})
            
            task.dependencies.add(dependency)
            return Response({
                'status': 'dependency added',
                'is_blocked': task.is_blocked()
            })
        except Task.DoesNotExist:
            return Response({'error': 'dependency task not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_dependency(self, request, pk=None):
        """Remove a dependency from this task"""
        task = self.get_object()
        dependency_id = request.data.get('dependency_id')
        
        if not dependency_id:
            return Response({'error': 'dependency_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            dependency = Task.objects.get(id=dependency_id)
            if task.dependencies.filter(id=dependency.id).exists():
                task.dependencies.remove(dependency)
                return Response({
                    'status': 'dependency removed',
                    'is_blocked': task.is_blocked()
                })
            else:
                return Response({'error': 'dependency not found for this task'}, status=status.HTTP_404_NOT_FOUND)
        except Task.DoesNotExist:
            return Response({'error': 'dependency task not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def dependencies(self, request, pk=None):
        """Get all dependencies for this task"""
        task = self.get_object()
        dependencies = task.dependencies.all()
        serializer = TaskSerializer(dependencies, many=True, context={'request': request})
        return Response({
            'is_blocked': task.is_blocked(),
            'dependencies': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def dependent_tasks(self, request, pk=None):
        """Get all tasks that depend on this task"""
        task = self.get_object()
        dependent_tasks = task.dependent_tasks.all()
        serializer = TaskSerializer(dependent_tasks, many=True, context={'request': request})
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommentAuthorOrProjectMember]

    def get_queryset(self):
        return Comment.objects.filter(
            task__task_list__project__in=Project.objects.filter(
                Q(owner=self.request.user) | Q(members=self.request.user)
            )
        )

class TaskAttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = TaskAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAttachmentUploaderOrProjectMember]

    def get_queryset(self):
        return TaskAttachment.objects.filter(
            task__task_list__project__in=Project.objects.filter(
                Q(owner=self.request.user) | Q(members=self.request.user)
            )
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def project_metrics(request, project_id):
    """
    Get metrics for a specific project
    """
    try:
        # Fix: Using filter with a Q object and then get the first object
        project = Project.objects.filter(
            id=project_id
        ).filter(
            Q(owner=request.user) | Q(members=request.user)
        ).first()
        
        if not project:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Get all tasks for this project
    tasks = Task.objects.filter(task_list__project=project)
    
    # Count tasks by status
    status_counts = tasks.values('status').annotate(count=Count('status'))
    
    # Count tasks by priority
    priority_counts = tasks.values('priority').annotate(count=Count('priority'))
    
    # Count tasks by assigned user
    assigned_counts = tasks.values(
        'assigned_to__username', 
        'assigned_to__id'
    ).annotate(count=Count('assigned_to'))
    
    # Calculate overdue tasks
    overdue_count = tasks.filter(
        status__in=['TODO', 'IN_PROGRESS', 'REVIEW'],
        due_date__lt=timezone.now()
    ).count()
    
    # Calculate completion rate
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='DONE').count()
    completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    
    # Count tasks due in the next week
    upcoming_tasks = tasks.filter(
        due_date__gte=timezone.now(),
        due_date__lte=timezone.now() + timezone.timedelta(days=7)
    ).count()
    
    # Average time to completion (for completed tasks with created_at)
    completed_tasks_with_dates = tasks.filter(
        status='DONE'
    ).exclude(updated_at=None)
    
    avg_completion_days = 0
    if completed_tasks_with_dates.exists():
        avg_completion_time_seconds = completed_tasks_with_dates.annotate(
            completion_time=F('updated_at') - F('created_at')
        ).aggregate(avg=Avg('completion_time'))['avg'].total_seconds()
        avg_completion_days = avg_completion_time_seconds / (60 * 60 * 24)
    
    return Response({
        "project_name": project.name,
        "total_tasks": total_tasks,
        "status_breakdown": status_counts,
        "priority_breakdown": priority_counts,
        "assigned_user_breakdown": assigned_counts,
        "overdue_tasks": overdue_count,
        "completion_rate": completion_rate,
        "upcoming_tasks": upcoming_tasks,
        "avg_completion_days": round(avg_completion_days, 1),
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_task_summary(request):
    """
    Get a summary of tasks for the current user
    """
    # Get all projects the user is a member of or owns
    projects = Project.objects.filter(
        Q(owner=request.user) | Q(members=request.user)
    )
    
    # Get all tasks assigned to the user
    assigned_tasks = Task.objects.filter(
        assigned_to=request.user,
        task_list__project__in=projects
    )
    
    # Get assigned tasks by status
    assigned_by_status = assigned_tasks.values('status').annotate(count=Count('status'))
    
    # Get overdue tasks
    overdue_tasks = assigned_tasks.filter(
        status__in=['TODO', 'IN_PROGRESS', 'REVIEW'],
        due_date__lt=timezone.now()
    )
    
    # Get tasks due today
    today_start = timezone.now().replace(hour=0, minute=0, second=0)
    today_end = today_start + timezone.timedelta(days=1)
    due_today = assigned_tasks.filter(
        due_date__gte=today_start,
        due_date__lt=today_end
    )
    
    # Get tasks due this week
    week_end = today_start + timezone.timedelta(days=7)
    due_this_week = assigned_tasks.filter(
        due_date__gte=today_end,
        due_date__lt=week_end
    )
    
    # Get recently completed tasks (last 7 days)
    recently_completed = assigned_tasks.filter(
        status='DONE',
        updated_at__gte=timezone.now() - timezone.timedelta(days=7)
    )
    
    return Response({
        "total_assigned": assigned_tasks.count(),
        "status_breakdown": assigned_by_status,
        "overdue_tasks": {
            "count": overdue_tasks.count(),
            "tasks": TaskSerializer(overdue_tasks, many=True).data
        },
        "due_today": {
            "count": due_today.count(),
            "tasks": TaskSerializer(due_today, many=True).data
        },
        "due_this_week": {
            "count": due_this_week.count(),
            "tasks": TaskSerializer(due_this_week, many=True).data
        },
        "recently_completed": {
            "count": recently_completed.count(),
            "tasks": TaskSerializer(recently_completed, many=True).data
        }
    })

# Template View Handlers - These functions render the HTML templates with appropriate context
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count, F, Q, Case, When, IntegerField
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse
import json

@login_required
def project_list_view(request):
    """Handle project listing and creation"""
    if request.method == 'POST':
        # Create new project
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if name:
            project = Project.objects.create(
                name=name,
                description=description,
                owner=request.user
            )
            project.members.add(request.user)
            messages.success(request, f'Project "{name}" created successfully.')
            return redirect('project-detail', pk=project.id)
        else:
            messages.error(request, 'Project name is required.')
    
    # Get all projects for the user
    projects = Project.objects.filter(
        Q(owner=request.user) | Q(members=request.user)
    ).distinct()
    
    # Get task statistics
    for project in projects:
        # Get all task lists for this project
        task_lists = TaskList.objects.filter(project=project)
        
        # Count all tasks
        task_count = Task.objects.filter(task_list__in=task_lists).count()
        
        # Count completed tasks
        completed_tasks = Task.objects.filter(
            task_list__in=task_lists,
            status='DONE'
        ).count()
        
        # Calculate completion percentage
        project.task_count = task_count
        project.completed_tasks = completed_tasks
        project.completion_percentage = (completed_tasks / task_count * 100) if task_count > 0 else 0
    
    return render(request, 'projects/project_list.html', {
        'projects': projects
    })

@login_required
def project_detail_view(request, pk):
    """Handle project detail view"""
    project = get_object_or_404(Project, id=pk)
    
    # Check if user has access to this project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        messages.error(request, 'You do not have access to this project.')
        return redirect('project-list')
    
    task_lists = project.task_lists.all().prefetch_related('tasks')
    
    # Calculate completion percentage
    total_tasks = 0
    completed_tasks = 0
    
    for task_list in task_lists:
        task_list_total = task_list.tasks.count()
        task_list_completed = task_list.tasks.filter(status='DONE').count()
        
        total_tasks += task_list_total
        completed_tasks += task_list_completed
    
    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    return render(request, 'projects/project_detail.html', {
        'project': project,
        'task_lists': task_lists,
        'completion_percentage': completion_percentage
    })

@login_required
def project_update_view(request, pk):
    """Handle project updates"""
    project = get_object_or_404(Project, id=pk)
    
    # Only project owner can update
    if project.owner != request.user:
        messages.error(request, 'Only the project owner can update project details.')
        return redirect('project-detail', pk=project.id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if name:
            project.name = name
            project.description = description
            project.save()
            messages.success(request, 'Project updated successfully.')
        else:
            messages.error(request, 'Project name is required.')
    
    return redirect('project-detail', pk=project.id)

@login_required
def project_delete_view(request, pk):
    """Handle project deletion"""
    project = get_object_or_404(Project, id=pk)
    
    # Only project owner can delete
    if project.owner != request.user:
        messages.error(request, 'Only the project owner can delete the project.')
        return redirect('project-detail', pk=project.id)
    
    if request.method == 'POST':
        project_name = project.name
        project.delete()
        messages.success(request, f'Project "{project_name}" has been deleted.')
    
    return redirect('project-list')

@login_required
def project_add_member_view(request, pk):
    """Handle adding members to a project"""
    project = get_object_or_404(Project, id=pk)
    
    # Only project owner can add members
    if project.owner != request.user:
        messages.error(request, 'Only the project owner can add members.')
        return redirect('project-detail', pk=project.id)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        
        if username:
            try:
                user = User.objects.get(username=username)
                if user == request.user:
                    messages.info(request, 'You are already a member of this project.')
                elif project.members.filter(id=user.id).exists():
                    messages.info(request, f'{username} is already a member of this project.')
                else:
                    project.members.add(user)
                    messages.success(request, f'{username} has been added to the project.')
            except User.DoesNotExist:
                messages.error(request, f'User {username} not found.')
        else:
            messages.error(request, 'Username is required.')
    
    return redirect('project-detail', pk=project.id)

@login_required
def tasklist_create_view(request):
    """Handle task list creation"""
    if request.method == 'POST':
        name = request.POST.get('name')
        project_id = request.POST.get('project')
        
        if name and project_id:
            try:
                project = Project.objects.get(id=project_id)
                
                # Check if user has access to this project
                if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
                    messages.error(request, 'You do not have access to this project.')
                    return redirect('project-list')
                
                # Get max position for new list
                max_position = TaskList.objects.filter(project=project).aggregate(max_pos=models.Max('position'))
                position = 1
                if max_position['max_pos'] is not None:
                    position = max_position['max_pos'] + 1
                
                TaskList.objects.create(
                    name=name,
                    project=project,
                    position=position
                )
                
                messages.success(request, f'Task list "{name}" created successfully.')
                return redirect('project-detail', pk=project_id)
            except Project.DoesNotExist:
                messages.error(request, 'Project not found.')
        else:
            messages.error(request, 'Task list name and project are required.')
    
    return redirect('project-list')

@login_required
def task_detail_view(request, pk):
    """Handle task detail view"""
    task = get_object_or_404(Task, id=pk)
    
    # Check if user has access to this task's project
    project = task.task_list.project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        messages.error(request, 'You do not have access to this task.')
        return redirect('project-list')
    
    # Get task comments and attachments
    comments = task.comments.all().order_by('-created_at')
    attachments = task.attachments.all().order_by('-created_at')
    
    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'comments': comments,
        'attachments': attachments,
    })

@login_required
def task_update_view(request, pk):
    """Handle task updates"""
    task = get_object_or_404(Task, id=pk)
    
    # Check if user has access to this task's project
    project = task.task_list.project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        messages.error(request, 'You do not have access to this task.')
        return redirect('project-list')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        status = request.POST.get('status')
        priority = request.POST.get('priority')
        due_date = request.POST.get('due_date') or None
        assigned_to_id = request.POST.get('assigned_to') or None
        task_list_id = request.POST.get('task_list')
        
        if title and status and priority and task_list_id:
            # Verify task list belongs to same project
            try:
                task_list = TaskList.objects.get(id=task_list_id, project=project)
                
                task.title = title
                task.description = description
                task.status = status
                task.priority = priority
                task.due_date = due_date
                task.task_list = task_list
                
                if assigned_to_id:
                    try:
                        assigned_to = User.objects.get(id=assigned_to_id)
                        # Verify assigned user is a project member
                        if project.owner == assigned_to or project.members.filter(id=assigned_to.id).exists():
                            task.assigned_to = assigned_to
                        else:
                            messages.warning(request, 'Assigned user must be a project member.')
                    except User.DoesNotExist:
                        messages.warning(request, 'Assigned user not found.')
                else:
                    task.assigned_to = None
                
                task.save()
                messages.success(request, 'Task updated successfully.')
            except TaskList.DoesNotExist:
                messages.error(request, 'Invalid task list selected.')
        else:
            messages.error(request, 'Task title, status, priority and task list are required.')
    
    return redirect('task-detail', pk=task.id)

@login_required
def task_delete_view(request, pk):
    """Handle task deletion"""
    task = get_object_or_404(Task, id=pk)
    
    # Check if user has access to this task's project
    project = task.task_list.project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        messages.error(request, 'You do not have access to this task.')
        return redirect('project-list')
    
    if request.method == 'POST':
        project_id = project.id
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" has been deleted.')
        return redirect('project-detail', pk=project_id)
    
    return redirect('task-detail', pk=task.id)

@login_required
def task_add_comment_view(request, pk):
    """Handle adding comments to a task"""
    task = get_object_or_404(Task, id=pk)
    
    # Check if user has access to this task's project
    project = task.task_list.project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        messages.error(request, 'You do not have access to this task.')
        return redirect('project-list')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        
        if content:
            Comment.objects.create(
                task=task,
                author=request.user,
                content=content
            )
            messages.success(request, 'Comment added successfully.')
        else:
            messages.error(request, 'Comment content is required.')
    
    return redirect('task-detail', pk=task.id)

def register_view(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('project-list')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            
            # For AJAX requests, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Account created for {username}. You can now log in.',
                    'redirect_url': reverse('login')
                })
            
            # For regular form submissions
            messages.success(request, f'Account created for {username}. You can now log in.')
            return redirect('login')
        else:
            # For AJAX requests, return errors as JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Please correct the errors below.',
                    'errors': form.errors.get_json_data()
                })
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile_view(request):
    """Handle user profile view and updates"""
    user = request.user
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        if username and email:
            # Check if username already exists for another user
            if User.objects.exclude(id=user.id).filter(username=username).exists():
                messages.error(request, 'Username already taken.')
            else:
                user.username = username
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.save()
                messages.success(request, 'Profile updated successfully.')
        else:
            messages.error(request, 'Username and email are required.')
    
    # Get user statistics
    assigned_tasks_count = Task.objects.filter(assigned_to=user).count()
    completed_tasks_count = Task.objects.filter(assigned_to=user, status='DONE').count()
    overdue_tasks_count = Task.objects.filter(
        assigned_to=user,
        status__in=['TODO', 'IN_PROGRESS', 'REVIEW'],
        due_date__lt=timezone.now()
    ).count()
    owned_projects_count = Project.objects.filter(owner=user).count()
    
    return render(request, 'users/profile.html', {
        'user': user,
        'assigned_tasks_count': assigned_tasks_count,
        'completed_tasks_count': completed_tasks_count,
        'overdue_tasks_count': overdue_tasks_count,
        'owned_projects_count': owned_projects_count,
    })

@login_required
def user_tasks_view(request):
    """Handle user task summary view"""
    # Get API response data
    response_data = user_task_summary(request).data
    
    # Calculate percentages for status breakdown
    status_breakdown = response_data.get('status_breakdown', [])
    total_tasks = response_data.get('total_assigned', 0)
    
    if total_tasks > 0:
        for status in status_breakdown:
            status['percentage'] = (status['count'] / total_tasks) * 100
    
    return render(request, 'tasks/user_task_summary.html', response_data)

def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('project-list')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember') == 'on'
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # If "remember me" is not checked, set session to expire when browser closes
                if not remember:
                    request.session.set_expiry(0)
                
                # For AJAX requests, return JSON response
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'Welcome back, {user.username}!',
                        'redirect_url': reverse('project-list')
                    })
                
                # For regular form submissions
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('project-list')
            else:
                # For AJAX requests, return errors as JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid username or password.',
                        'errors': {
                            'non_field_errors': ['Invalid username or password.']
                        }
                    })
                
                # For regular form submissions
                messages.error(request, 'Invalid username or password.')
        else:
            # For AJAX requests, return errors as JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Please enter both username and password.',
                    'errors': {
                        'username': ['This field is required.'] if not username else [],
                        'password': ['This field is required.'] if not password else []
                    }
                })
            
            # For regular form submissions
            if not username:
                messages.error(request, 'Username is required.')
            if not password:
                messages.error(request, 'Password is required.')
    
    return render(request, 'users/login.html')