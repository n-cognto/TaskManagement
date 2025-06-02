from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
import uuid
from datetime import timedelta

class Project(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects', db_index=True)
    members = models.ManyToManyField(User, related_name='project_members', blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['owner', 'created_at']),
        ]

    def __str__(self):
        return self.name

class TaskList(models.Model):
    name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='task_lists', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ['position']
        indexes = [
            models.Index(fields=['project', 'position']),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.name}"

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('REVIEW', 'In Review'),
        ('DONE', 'Done'),
    ]

    title = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)
    task_list = models.ForeignKey(TaskList, on_delete=models.CASCADE, related_name='tasks', db_index=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks', db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO', db_index=True)
    due_date = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    position = models.IntegerField(default=0)
    dependencies = models.ManyToManyField('self', symmetrical=False, related_name='dependent_tasks', blank=True)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['position']
        indexes = [
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['task_list', 'position']),
            models.Index(fields=['priority', 'status']),
        ]

    def __str__(self):
        return self.title

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store original state to detect changes
        if self.pk:
            self._previous_assignee = self.assigned_to
            self._previous_status = self.status
    
    def is_blocked(self):
        """Check if this task is blocked by unfinished dependencies"""
        return self.dependencies.exclude(status='DONE').exists()
    
    def can_start(self):
        """Check if this task can be started based on dependencies"""
        return not self.is_blocked()
    
    def get_blocking_tasks(self):
        """Get list of dependencies that are not completed yet"""
        return self.dependencies.exclude(status='DONE')

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', 'created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"

class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments', db_index=True)
    file = models.FileField(upload_to='task_attachments/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    file_name = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['task', 'uploaded_at']),
        ]

    def __str__(self):
        return self.file_name

class ActivityLog(models.Model):
    """Model to track all changes to tasks and projects"""
    
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('ASSIGN', 'Assigned'),
        ('STATUS', 'Status Changed'),
        ('COMMENT', 'Commented'),
        ('ATTACHMENT', 'Attachment Added'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['task']),
            models.Index(fields=['project']),
            models.Index(fields=['user']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.get_action_display()} {self.task or self.project} at {self.timestamp}"

@receiver(pre_save, sender=Task)
def task_pre_save(sender, instance, **kwargs):
    """Store the previous state of important task fields before saving"""
    if instance.pk:
        try:
            old_instance = Task.objects.get(pk=instance.pk)
            instance._previous_assignee = old_instance.assigned_to
            instance._previous_status = old_instance.status
            
            # Store all previous values for activity logging
            instance._previous_values = {
                'title': old_instance.title,
                'description': old_instance.description,
                'priority': old_instance.priority,
                'status': old_instance.status,
                'due_date': old_instance.due_date,
                'assigned_to': old_instance.assigned_to,
                'task_list': old_instance.task_list,
                'estimated_hours': old_instance.estimated_hours,
                'actual_hours': old_instance.actual_hours,
            }
        except Task.DoesNotExist:
            pass

@receiver(post_save, sender=Task)
def task_post_save(sender, instance, created, **kwargs):
    """Log task creation and updates"""
    # We need request.user, which is not available in signals
    # Actual logging will be done in the views

@receiver(post_save, sender=Comment)
def comment_post_save(sender, instance, created, **kwargs):
    """Log comment creation"""
    if created:
        ActivityLog.objects.create(
            user=instance.author,
            task=instance.task,
            action='COMMENT',
            description=f"Added comment on task '{instance.task.title}'",
            new_value=instance.content[:100] + ('...' if len(instance.content) > 100 else '')
        )

@receiver(post_save, sender=TaskAttachment)
def attachment_post_save(sender, instance, created, **kwargs):
    """Log attachment creation"""
    if created:
        ActivityLog.objects.create(
            user=instance.uploaded_by,
            task=instance.task,
            action='ATTACHMENT',
            description=f"Added attachment to task '{instance.task.title}'",
            new_value=instance.file_name
        )

class EmailVerification(models.Model):
    """Model to store email verification tokens"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    def is_valid(self):
        """Check if token is still valid (expires after 48 hours)"""
        expiry_time = self.created_at + timedelta(hours=48)
        return timezone.now() <= expiry_time
    
    def __str__(self):
        return f"Email verification for {self.user.username}"