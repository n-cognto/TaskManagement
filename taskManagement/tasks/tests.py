from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
import json
from .models import Project, TaskList, Task, Comment, TaskAttachment

class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            description='Test Description',
            owner=self.user
        )
    
    def test_project_creation(self):
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.description, 'Test Description')
        self.assertEqual(self.project.owner, self.user)
        self.assertTrue(isinstance(self.project, Project))
        self.assertEqual(str(self.project), 'Test Project')

class TaskListModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            owner=self.user
        )
        self.task_list = TaskList.objects.create(
            name='Test List',
            project=self.project,
            position=1
        )
    
    def test_task_list_creation(self):
        self.assertEqual(self.task_list.name, 'Test List')
        self.assertEqual(self.task_list.project, self.project)
        self.assertEqual(self.task_list.position, 1)
        self.assertTrue(isinstance(self.task_list, TaskList))
        self.assertEqual(str(self.task_list), f"{self.project.name} - {self.task_list.name}")

class TaskModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            owner=self.user
        )
        self.task_list = TaskList.objects.create(
            name='Test List',
            project=self.project
        )
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            task_list=self.task_list,
            created_by=self.user,
            priority='HIGH',
            status='TODO',
            due_date=timezone.now() + timezone.timedelta(days=1)
        )
    
    def test_task_creation(self):
        self.assertEqual(self.task.title, 'Test Task')
        self.assertEqual(self.task.description, 'Test Description')
        self.assertEqual(self.task.task_list, self.task_list)
        self.assertEqual(self.task.created_by, self.user)
        self.assertEqual(self.task.priority, 'HIGH')
        self.assertEqual(self.task.status, 'TODO')
        self.assertTrue(self.task.due_date > timezone.now())
        self.assertTrue(isinstance(self.task, Task))
        self.assertEqual(str(self.task), 'Test Task')

class CommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            owner=self.user
        )
        self.task_list = TaskList.objects.create(
            name='Test List',
            project=self.project
        )
        self.task = Task.objects.create(
            title='Test Task',
            task_list=self.task_list,
            created_by=self.user
        )
        self.comment = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Test Comment'
        )
    
    def test_comment_creation(self):
        self.assertEqual(self.comment.task, self.task)
        self.assertEqual(self.comment.author, self.user)
        self.assertEqual(self.comment.content, 'Test Comment')
        self.assertTrue(isinstance(self.comment, Comment))
        self.assertEqual(str(self.comment), f"Comment by {self.user.username} on {self.task.title}")

class ProjectAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.project_data = {
            'name': 'API Test Project',
            'description': 'Created via API'
        }
        
    def test_create_project(self):
        response = self.client.post(
            '/api/projects/',
            self.project_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Project.objects.get().name, 'API Test Project')
        
    def test_get_projects(self):
        Project.objects.create(name='Test Project 1', owner=self.user)
        Project.objects.create(name='Test Project 2', owner=self.user)
        
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
    def test_get_project_detail(self):
        project = Project.objects.create(
            name='Test Project',
            description='Test Description',
            owner=self.user
        )
        
        response = self.client.get(f'/api/projects/{project.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Project')
        
    def test_update_project(self):
        project = Project.objects.create(
            name='Old Project Name',
            description='Old Description',
            owner=self.user
        )
        
        updated_data = {
            'name': 'Updated Project Name',
            'description': 'Updated Description'
        }
        
        response = self.client.patch(
            f'/api/projects/{project.id}/',
            updated_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.name, 'Updated Project Name')
        self.assertEqual(project.description, 'Updated Description')
        
    def test_delete_project(self):
        project = Project.objects.create(
            name='Project to Delete',
            owner=self.user
        )
        
        response = self.client.delete(f'/api/projects/{project.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 0)
