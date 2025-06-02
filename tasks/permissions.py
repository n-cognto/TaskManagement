from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user

class IsProjectOwnerOrMember(permissions.BasePermission):
    """
    Custom permission to only allow owners or members of a project to access its details.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is owner or member of the project
        return obj.owner == request.user or request.user in obj.members.all()

class IsTaskListProjectOwnerOrMember(permissions.BasePermission):
    """
    Custom permission to only allow owners or members of a project to access its task lists.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is owner or member of the project that the task list belongs to
        return obj.project.owner == request.user or request.user in obj.project.members.all()

class IsTaskProjectOwnerOrMember(permissions.BasePermission):
    """
    Custom permission to only allow owners or members of a project to access its tasks.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is owner or member of the project that the task belongs to
        project = obj.task_list.project
        return project.owner == request.user or request.user in project.members.all()

class IsCommentAuthorOrProjectMember(permissions.BasePermission):
    """
    Custom permission to only allow comment authors to edit their comments,
    and project owners/members to view all comments.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to project owners and members
        project = obj.task.task_list.project
        if request.method in permissions.SAFE_METHODS:
            return project.owner == request.user or request.user in project.members.all()

        # Write permissions are only allowed to the author of the comment
        return obj.author == request.user

class IsAttachmentUploaderOrProjectMember(permissions.BasePermission):
    """
    Custom permission to only allow attachment uploaders to delete their attachments,
    and project owners/members to view all attachments.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to project owners and members
        project = obj.task.task_list.project
        if request.method in permissions.SAFE_METHODS:
            return project.owner == request.user or request.user in project.members.all()

        # Write permissions are only allowed to the uploader of the attachment
        # or the project owner
        return obj.uploaded_by == request.user or project.owner == request.user