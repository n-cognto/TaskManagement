import django_filters
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Project, TaskList, Task

class ProjectFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    member = django_filters.ModelChoiceFilter(queryset=User.objects.all(), field_name='members')
    
    class Meta:
        model = Project
        fields = ['name', 'description', 'owner', 'members']

class TaskListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    project = django_filters.NumberFilter(field_name='project__id')
    project_name = django_filters.CharFilter(field_name='project__name', lookup_expr='icontains')
    
    class Meta:
        model = TaskList
        fields = ['name', 'project', 'position']

class TaskFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    project = django_filters.NumberFilter(field_name='task_list__project__id')
    task_list = django_filters.NumberFilter(field_name='task_list__id')
    status = django_filters.MultipleChoiceFilter(choices=Task.STATUS_CHOICES)
    priority = django_filters.MultipleChoiceFilter(choices=Task.PRIORITY_CHOICES)
    assigned_to = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    created_by = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    due_date_from = django_filters.DateFilter(field_name='due_date', lookup_expr='gte')
    due_date_to = django_filters.DateFilter(field_name='due_date', lookup_expr='lte')
    no_due_date = django_filters.BooleanFilter(field_name='due_date', lookup_expr='isnull')
    unassigned = django_filters.BooleanFilter(field_name='assigned_to', lookup_expr='isnull')
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'task_list', 'status', 
            'priority', 'assigned_to', 'created_by'
        ]