from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase as DRFAPITestCase, APIClient
from rest_framework import status

from .models import Project, Task


class ModelTestClass(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass', email='test@example.com')
        self.project = Project.objects.create(
            name='Test Project',
            description='Test Description',
            created_by=self.user
        )

    def test_project_creation(self):
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.created_by, self.user)
        self.assertEqual(str(self.project), 'Test Project')

    def test_task_creation(self):
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            project=self.project,
            status=Task.StatusChoices.PENDING,
            created_by=self.user,
            assigned_to=self.user,
            due_date=timezone.now() + timedelta(days=1)
        )
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.status, Task.StatusChoices.PENDING)
        self.assertEqual(str(task), 'Test Task')

    def test_task_is_overdue_property(self):
        overdue_task = Task.objects.create(
            title='Overdue Task',
            description='Test',
            project=self.project,
            status=Task.StatusChoices.IN_PROGRESS,
            due_date=timezone.now() - timedelta(hours=1),
            created_by=self.user
        )
        self.assertTrue(overdue_task.is_overdue)

        future_task = Task.objects.create(
            title='Future Task',
            description='Test',
            project=self.project,
            status=Task.StatusChoices.PENDING,
            due_date=timezone.now() + timedelta(hours=1),
            created_by=self.user
        )
        self.assertFalse(future_task.is_overdue)

        completed_task = Task.objects.create(
            title='Completed Task',
            description='Test',
            project=self.project,
            status=Task.StatusChoices.COMPLETED,
            due_date=timezone.now() - timedelta(hours=1),
            created_by=self.user
        )
        self.assertFalse(completed_task.is_overdue)


class TaskAPITestClass(DRFAPITestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.default_format = 'json'
        self.user = User.objects.create_user(
            username='testuser', password='testpass', email='test@example.com')
        self.admin_user = User.objects.create_superuser(
            username='adminuser', password='adminpass', email='admin@example.com')
        self.client.force_authenticate(user=self.user)

        self.project = Project.objects.create(
            name='API Test Project',
            description='Testing API',
            created_by=self.user
        )

        self.task = Task.objects.create(
            title='API Test Task',
            description='Testing API endpoints',
            project=self.project,
            status=Task.StatusChoices.PENDING,
            created_by=self.user,
            assigned_to=self.user,
            due_date=timezone.now() + timedelta(days=1)
        )

    def test_list_tasks(self):
        response = self.client.get('/tasks/', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_task(self):
        initial_count = Task.objects.count()
        data = {
            'title': 'New Task',
            'description': 'New task description',
            'project': self.project.id,
            'status': 'PENDING',
            'assigned_to': self.user.id,
            'due_date': (timezone.now() + timedelta(days=2)).isoformat()
        }
        response = self.client.post(
            '/tasks/', data, format='json', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), initial_count + 1)
        self.assertEqual(response.data['title'], 'New Task')

    def test_retrieve_task(self):
        url = f'/tasks/{self.task.pk}/'
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('title', response.data)

    def test_update_task_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = f'/tasks/{self.task.pk}/'
        data = {'title': 'Updated Task Title'}
        response = self.client.patch(
            url, data, format='json', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task Title')

    def test_update_task_as_regular_user_forbidden(self):
        url = f'/tasks/{self.task.pk}/'
        data = {'title': 'Updated Task Title'}
        response = self.client.patch(
            url, data, format='json', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_task_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        task_id = self.task.pk
        url = f'/tasks/{task_id}/'
        response = self.client.delete(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=task_id).exists())

    def test_delete_task_as_regular_user_forbidden(self):
        task_id = self.task.pk
        url = f'/tasks/{task_id}/'
        response = self.client.delete(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Task.objects.filter(id=task_id).exists())

    def test_authentication_required(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/tasks/', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_endpoint(self):
        response = self.client.get(
            '/tasks/dashboard/', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ProjectAPITestClass(DRFAPITestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.default_format = 'json'
        self.user = User.objects.create_user(
            username='projectuser', password='testpass', email='project@example.com')
        self.admin_user = User.objects.create_superuser(
            username='projectadmin', password='adminpass', email='padmin@example.com')
        self.client.force_authenticate(user=self.user)

        self.project = Project.objects.create(
            name='Test Project',
            description='Test project description',
            created_by=self.user
        )

    def test_list_projects(self):
        response = self.client.get(
            '/projects/', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_project(self):
        initial_count = Project.objects.count()
        data = {
            'name': 'New Project',
            'description': 'New project description'
        }
        response = self.client.post(
            '/projects/', data, format='json', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), initial_count + 1)
        self.assertEqual(response.data['name'], 'New Project')

    def test_retrieve_project(self):
        url = f'/projects/{self.project.pk}/'
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Project')

    def test_update_project_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = f'/projects/{self.project.pk}/'
        data = {'name': 'Updated Project Name'}
        response = self.client.patch(
            url, data, format='json', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated Project Name')

    def test_update_project_as_regular_user_forbidden(self):
        url = f'/projects/{self.project.pk}/'
        data = {'name': 'Updated Project Name'}
        response = self.client.patch(
            url, data, format='json', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_project_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        project_id = self.project.pk
        url = f'/projects/{project_id}/'
        response = self.client.delete(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(id=project_id).exists())

    def test_delete_project_as_regular_user_forbidden(self):
        project_id = self.project.pk
        url = f'/projects/{project_id}/'
        response = self.client.delete(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Project.objects.filter(id=project_id).exists())


class FilterAPITestClass(DRFAPITestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.default_format = 'json'
        self.user = User.objects.create_user(
            username='filteruser', password='testpass')
        self.client.force_authenticate(user=self.user)

        Task.objects.all().delete()
        Project.objects.all().delete()

        self.project1 = Project.objects.create(
            name='Backend Project', created_by=self.user)
        self.project2 = Project.objects.create(
            name='Frontend Project', created_by=self.user)

        self.pending_task = Task.objects.create(
            title='Pending Task',
            description='Test',
            project=self.project1,
            status=Task.StatusChoices.PENDING,
            created_by=self.user,
            due_date=timezone.now() + timedelta(hours=12)
        )
        self.in_progress_task = Task.objects.create(
            title='In Progress Task',
            description='Test',
            project=self.project1,
            status=Task.StatusChoices.IN_PROGRESS,
            created_by=self.user,
            due_date=timezone.now() + timedelta(hours=2)
        )
        self.completed_task = Task.objects.create(
            title='Completed Task',
            description='Test',
            project=self.project2,
            status=Task.StatusChoices.COMPLETED,
            created_by=self.user,
            due_date=timezone.now() - timedelta(hours=5)
        )
        self.overdue_task = Task.objects.create(
            title='Overdue Task',
            description='Test',
            project=self.project2,
            status=Task.StatusChoices.PENDING,
            created_by=self.user,
            due_date=timezone.now() - timedelta(hours=1)
        )

    def test_filter_by_status(self):
        response = self.client.get(
            '/tasks/?status=PENDING', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pending_count = len(
            [t for t in response.data if t['status'] == 'PENDING'])
        self.assertEqual(pending_count, 2)

    def test_filter_by_project(self):
        response = self.client.get(
            f'/tasks/?project={self.project1.id}', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project1_count = len(
            [t for t in response.data if t['project'] == self.project1.id])
        self.assertEqual(project1_count, 2)

    def test_filter_by_project_name(self):
        response = self.client.get(
            '/tasks/?project_name=backend', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_filter_overdue_tasks(self):
        response = self.client.get(
            '/tasks/?is_overdue=true', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        overdue_count = len(
            [t for t in response.data if t.get('is_overdue', False)])
        self.assertGreaterEqual(overdue_count, 1)

    def test_filter_upcoming_deadlines(self):
        response = self.client.get(
            '/tasks/?due_date_upcoming=1', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_search_functionality(self):
        response = self.client.get(
            '/tasks/?search=pending', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_ordering_by_due_date(self):
        response = self.client.get(
            '/tasks/?ordering=due_date', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_ordering_by_created_at_desc(self):
        response = self.client.get(
            '/tasks/?ordering=-created_at', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)


class AuthenticationAPITestClass(DRFAPITestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.default_format = 'json'
        self.user = User.objects.create_user(
            username='authuser',
            password='authpass123',
            email='auth@example.com'
        )

    def test_login_with_valid_credentials(self):
        data = {
            'action': 'login',
            'username': 'authuser',
            'password': 'authpass123'
        }
        response = self.client.post(
            '/auth/auth/',
            data,
            format='json',
            HTTP_ACCEPT='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

    def test_login_with_invalid_credentials(self):
        data = {
            'action': 'login',
            'username': 'authuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(
            '/auth/auth/',
            data,
            format='json',
            HTTP_ACCEPT='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_register_new_user(self):
        data = {
            'action': 'register',
            'username': 'newuser',
            'password': 'newpass123',
            'email': 'newuser@example.com'
        }
        response = self.client.post(
            '/auth/auth/',
            data,
            format='json',
            HTTP_ACCEPT='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_existing_username(self):
        data = {
            'action': 'register',
            'username': 'authuser',
            'password': 'newpass123',
            'email': 'another@example.com'
        }
        response = self.client.post(
            '/auth/auth/',
            data,
            format='json',
            HTTP_ACCEPT='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
