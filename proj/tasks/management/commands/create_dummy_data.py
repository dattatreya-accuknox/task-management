from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from tasks.models import Project, Task


class Command(BaseCommand):
    help = 'Creates dummy data for testing: 2 users (1 admin, 1 regular), 2 projects, and 10 tasks'

    def handle(self, *args, **kwargs):
        if User.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING(
                'Dummy data already exists. Skipping creation.'))
            return

        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.stdout.write(self.style.SUCCESS(
            f'Created admin user: {admin_user.username}'))

        regular_user = User.objects.create_user(
            username='john',
            email='john@example.com',
            password='john123'
        )
        self.stdout.write(self.style.SUCCESS(
            f'Created regular user: {regular_user.username}'))

        project1 = Project.objects.create(
            name='Backend Development',
            description='Build REST APIs and backend services',
            created_by=admin_user
        )
        self.stdout.write(self.style.SUCCESS(
            f'Created project: {project1.name}'))

        project2 = Project.objects.create(
            name='Frontend Development',
            description='Build user interfaces and dashboards',
            created_by=admin_user
        )
        self.stdout.write(self.style.SUCCESS(
            f'Created project: {project2.name}'))

        now = timezone.now()

        tasks_data = [
            {
                'title': 'Setup Database Schema',
                'description': 'Create PostgreSQL database schema for the project',
                'project': project1,
                'assigned_to': admin_user,
                'created_by': admin_user,
                'status': Task.StatusChoices.COMPLETED,
                'due_date': now - timedelta(days=5)
            },
            {
                'title': 'Implement User Authentication',
                'description': 'Add JWT authentication to the API',
                'project': project1,
                'assigned_to': admin_user,
                'created_by': admin_user,
                'status': Task.StatusChoices.COMPLETED,
                'due_date': now - timedelta(days=3)
            },
            {
                'title': 'Create REST API Endpoints',
                'description': 'Build CRUD endpoints for tasks and projects',
                'project': project1,
                'assigned_to': regular_user,
                'created_by': admin_user,
                'status': Task.StatusChoices.IN_PROGRESS,
                'due_date': now + timedelta(days=2)
            },
            {
                'title': 'Add Filtering and Search',
                'description': 'Implement django-filter for API filtering',
                'project': project1,
                'assigned_to': regular_user,
                'created_by': admin_user,
                'status': Task.StatusChoices.PENDING,
                'due_date': now + timedelta(days=5)
            },
            {
                'title': 'Setup Celery Tasks',
                'description': 'Configure Celery for background task processing',
                'project': project1,
                'assigned_to': admin_user,
                'created_by': admin_user,
                'status': Task.StatusChoices.IN_PROGRESS,
                'due_date': now + timedelta(days=1)
            },
            {
                'title': 'Design Dashboard Layout',
                'description': 'Create wireframes and mockups for the dashboard',
                'project': project2,
                'assigned_to': regular_user,
                'created_by': admin_user,
                'status': Task.StatusChoices.COMPLETED,
                'due_date': now - timedelta(days=4)
            },
            {
                'title': 'Build Task List Component',
                'description': 'Create a reusable task list UI component',
                'project': project2,
                'assigned_to': regular_user,
                'created_by': admin_user,
                'status': Task.StatusChoices.IN_PROGRESS,
                'due_date': now + timedelta(hours=12)
            },
            {
                'title': 'Implement Project Management UI',
                'description': 'Build interface for creating and managing projects',
                'project': project2,
                'assigned_to': regular_user,
                'created_by': admin_user,
                'status': Task.StatusChoices.PENDING,
                'due_date': now + timedelta(days=3)
            },
            {
                'title': 'Add Form Validation',
                'description': 'Implement client-side validation for all forms',
                'project': project2,
                'assigned_to': admin_user,
                'created_by': admin_user,
                'status': Task.StatusChoices.PENDING,
                'due_date': now + timedelta(days=7)
            },
            {
                'title': 'Write Unit Tests',
                'description': 'Create comprehensive test suite for the application',
                'project': project1,
                'assigned_to': admin_user,
                'created_by': admin_user,
                'status': Task.StatusChoices.PENDING,
                'due_date': now + timedelta(days=10)
            },
        ]

        for task_data in tasks_data:
            task = Task.objects.create(**task_data)
            self.stdout.write(self.style.SUCCESS(
                f'Created task: {task.title}'))

        self.stdout.write(self.style.SUCCESS(
            '\n=== Dummy Data Created Successfully ==='))
        self.stdout.write(self.style.SUCCESS('\nLogin Credentials:'))
        self.stdout.write(self.style.SUCCESS(
            'Admin User: username=admin, password=admin123'))
        self.stdout.write(self.style.SUCCESS(
            'Regular User: username=john, password=john123'))
        self.stdout.write(self.style.SUCCESS(
            f'\nCreated {Project.objects.count()} projects'))
        self.stdout.write(self.style.SUCCESS(
            f'Created {Task.objects.count()} tasks'))
