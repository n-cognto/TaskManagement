# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Project, TaskList, Task, Comment, TaskAttachment

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'task', 'author', 'content', 'created_at', 'updated_at']
        read_only_fields = ['author']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class TaskAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = TaskAttachment
        fields = ['id', 'task', 'file', 'uploaded_by', 'uploaded_at', 'file_name']
        read_only_fields = ['uploaded_by']

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)

class TaskSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    assigned_to = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    is_blocked = serializers.BooleanField(read_only=True)
    blocking_tasks = serializers.SerializerMethodField()
    dependency_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Task.objects.all(),
        source='dependencies',
        required=False
    )

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'task_list', 'assigned_to', 
            'created_by', 'priority', 'status', 'due_date', 'created_at', 
            'updated_at', 'position', 'comments', 'attachments', 'dependencies',
            'dependency_ids', 'is_blocked', 'blocking_tasks', 'estimated_hours', 
            'actual_hours'
        ]
        read_only_fields = ['created_by']

    def get_blocking_tasks(self, obj):
        """Return simplified representation of blocking tasks"""
        blocking = obj.get_blocking_tasks()
        return [{'id': t.id, 'title': t.title, 'status': t.status} for t in blocking]
        
    def validate(self, attrs):
        """Validate task data including dependencies"""
        # Check for circular dependencies
        if 'dependencies' in attrs:
            task_id = self.instance.id if self.instance else None
            for dep in attrs['dependencies']:
                if dep.id == task_id:
                    raise serializers.ValidationError("A task cannot depend on itself")
                    
                # Check if this would create a circular dependency
                if task_id and dep.dependencies.filter(id=task_id).exists():
                    raise serializers.ValidationError(
                        f"Adding dependency on task {dep.id} would create a circular dependency"
                    )
                    
        return attrs

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        dependencies = validated_data.pop('dependencies', [])
        task = super().create(validated_data)
        task.dependencies.set(dependencies)
        return task
        
    def update(self, instance, validated_data):
        dependencies = validated_data.pop('dependencies', None)
        task = super().update(instance, validated_data)
        if dependencies is not None:
            task.dependencies.set(dependencies)
        return task

class TaskListSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = TaskList
        fields = ['id', 'name', 'project', 'created_at', 'position', 'tasks']

class ProjectSerializer(serializers.ModelSerializer):
    task_lists = TaskListSerializer(many=True, read_only=True)
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'created_at', 'owner', 'members', 'task_lists']
        read_only_fields = ['owner']

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
