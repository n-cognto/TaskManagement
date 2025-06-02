# TaskManagement API

A comprehensive task management system built with Django and Django REST Framework. The system allows users to create projects, organize tasks in lists, assign tasks to users, attach files, and add comments.

## Features

- **Project Management**: Create, update, and delete projects
- **Task Organization**: Organize tasks into task lists within projects
- **Task Assignment**: Assign tasks to project members
- **Task Prioritization**: Set task priorities and track status
- **Comments & Attachments**: Add comments and file attachments to tasks
- **User Authentication**: JWT-based authentication for secure API access
- **Analytics & Reporting**: Get insights into project and task metrics
- **API Documentation**: Interactive API documentation with Swagger UI
- **Docker Support**: Easy deployment with Docker and Docker Compose

## Installation

### Prerequisites

- Python 3.10+
- pip
- Virtual environment (recommended)
- PostgreSQL (optional, can use SQLite for development)
- Docker & Docker Compose (optional, for containerized deployment)

### Local Development Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/TaskManagement.git
   cd TaskManagement/taskManagement
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Copy `.env.example` to `.env` (if not already created)
   - Uncomment the SQLite line for local development
   - Set any other required environment variables

5. Run migrations:
   ```
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

8. Access the API at http://127.0.0.1:8000/api/
   - API documentation: http://127.0.0.1:8000/swagger/
   - Admin interface: http://127.0.0.1:8000/admin/

### Docker Deployment

1. Make sure Docker and Docker Compose are installed on your system

2. Configure environment variables in the `.env` file
   - Make sure to use the PostgreSQL DATABASE_URL

3. Build and run the containers:
   ```
   docker-compose up -d --build
   ```

4. Create a superuser:
   ```
   docker-compose exec web python manage.py createsuperuser
   ```

5. Access the API at http://localhost:8000/api/
   - API documentation: http://localhost:8000/swagger/
   - Admin interface: http://localhost:8000/admin/

## API Endpoints

### Authentication

- `POST /api/token/`: Get JWT token pair
- `POST /api/token/refresh/`: Refresh JWT access token
- `POST /api/token/verify/`: Verify JWT token

### User Management

- `POST /api/register/`: Register a new user
- `GET /api/profile/`: Get current user profile
- `PUT /api/profile/`: Update current user profile

### Projects

- `GET /api/projects/`: List all projects accessible to the user
- `POST /api/projects/`: Create a new project
- `GET /api/projects/{id}/`: Get project details
- `PUT /api/projects/{id}/`: Update project
- `DELETE /api/projects/{id}/`: Delete project
- `POST /api/projects/{id}/add_member/`: Add a member to the project

### Task Lists

- `GET /api/tasklists/`: List all task lists
- `POST /api/tasklists/`: Create a new task list
- `GET /api/tasklists/{id}/`: Get task list details
- `PUT /api/tasklists/{id}/`: Update task list
- `DELETE /api/tasklists/{id}/`: Delete task list

### Tasks

- `GET /api/tasks/`: List all tasks
- `POST /api/tasks/`: Create a new task
- `GET /api/tasks/{id}/`: Get task details
- `PUT /api/tasks/{id}/`: Update task
- `DELETE /api/tasks/{id}/`: Delete task
- `POST /api/tasks/{id}/assign/`: Assign task to a user
- `POST /api/tasks/{id}/update_position/`: Update task position

### Analytics

- `GET /api/projects/{id}/metrics/`: Get project metrics
- `GET /api/user/task-summary/`: Get user task summary

## Filtering and Searching

The API supports filtering, searching, and ordering on most endpoints:

- Filtering: `?status=TODO&priority=HIGH`
- Searching: `?search=project name`
- Ordering: `?ordering=due_date`

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.