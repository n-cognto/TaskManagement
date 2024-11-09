from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Project, TaskList, Task, Comment, TaskAttachment

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'members']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'members': forms.SelectMultiple(attrs={'class': 'select2'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Exclude the current user from the members field
            self.fields['members'].queryset = User.objects.exclude(id=user.id)
        
        # Add custom classes for styling
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

class TaskListForm(forms.ModelForm):
    class Meta:
        model = TaskList
        fields = ['name', 'position']
        widgets = {
            'position': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

class TaskForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'assigned_to', 'priority',
            'status', 'due_date', 'position'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'position': forms.NumberInput(attrs={'min': 0}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        task_list = kwargs.pop('task_list', None)
        super().__init__(*args, **kwargs)
        
        if task_list:
            # Only show members of the related project as possible assignees
            self.fields['assigned_to'].queryset = task_list.project.members.all()
        
        for field in self.fields:
            if field not in ['priority', 'status']:  # These already have form-select class
                self.fields[field].widget.attrs['class'] = 'form-control'

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now():
            raise ValidationError("Due date cannot be in the past.")
        return due_date

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Write your comment here...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs['class'] = 'form-control'

class TaskAttachmentForm(forms.ModelForm):
    class Meta:
        model = TaskAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'})
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Limit file size to 10MB
            if file.size > 10 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 10MB.")
            
            # Check file extension
            allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.txt']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(f"Only the following file types are allowed: {', '.join(allowed_extensions)}")
        return file

class TaskBulkUpdateForm(forms.Form):
    tasks = forms.ModelMultipleChoiceField(
        queryset=Task.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )
    status = forms.ChoiceField(
        choices=[('', '----')] + list(Task.STATUS_CHOICES),
        required=False
    )
    priority = forms.ChoiceField(
        choices=[('', '----')] + list(Task.PRIORITY_CHOICES),
        required=False
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label="----"
    )

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        if project:
            self.fields['tasks'].queryset = Task.objects.filter(
                task_list__project=project
            )
            self.fields['assigned_to'].queryset = project.members.all()

class TaskFilterForm(forms.Form):
    status = forms.MultipleChoiceField(
        choices=Task.STATUS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    priority = forms.MultipleChoiceField(
        choices=Task.PRIORITY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    assigned_to = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    due_date_start = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    due_date_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        if project:
            self.fields['assigned_to'].queryset = project.members.all()