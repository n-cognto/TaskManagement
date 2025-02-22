# views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Project, TaskList, Task, Comment, TaskAttachment
from .serializers import (
    ProjectSerializer, TaskListSerializer, TaskSerializer,
    CommentSerializer, TaskAttachmentSerializer, UserSerializer
)

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
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
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['position', 'created_at']

    def get_queryset(self):
        return TaskList.objects.filter(
            project__in=Project.objects.filter(
                Q(owner=self.request.user) | Q(members=self.request.user)
            )
        )

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
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

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(
            task__task_list__project__in=Project.objects.filter(
                Q(owner=self.request.user) | Q(members=self.request.user)
            )
        )

class TaskAttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = TaskAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TaskAttachment.objects.filter(
            task__task_list__project__in=Project.objects.filter(
                Q(owner=self.request.user) | Q(members=self.request.user)
            )
        )
        
        
