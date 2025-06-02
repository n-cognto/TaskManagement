from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class LoginRateThrottle(AnonRateThrottle):
    """
    Throttle class for login attempts to prevent brute force attacks
    """
    scope = 'api_login'

class RegistrationRateThrottle(AnonRateThrottle):
    """
    Throttle class for registration attempts to prevent abuse
    """
    scope = 'api_register'

class ProjectDetailRateThrottle(UserRateThrottle):
    """
    Throttle for project detail API
    """
    scope = 'user'

class TaskDetailRateThrottle(UserRateThrottle):
    """
    Throttle for task detail API
    """
    scope = 'user'