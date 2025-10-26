from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .filters import ProjectFilter, TaskFilter
from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    @action(detail=False, methods=['get', 'post'], url_path='auth')
    def auth_page(self, request):
        if request.user.is_authenticated:
            return redirect('task-dashboard')

        if request.method == 'POST':
            action_type = request.POST.get(
                'action') or request.data.get('action')

            if action_type == 'login':
                username = request.POST.get(
                    'username') or request.data.get('username')
                password = request.POST.get(
                    'password') or request.data.get('password')

                user = authenticate(
                    request, username=username, password=password)

                if user is not None:
                    if request.accepted_renderer.format == 'html':
                        login(request, user)
                        return redirect('task-dashboard')

                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'message': 'Login successful',
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'is_staff': user.is_staff
                        },
                        'tokens': {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token)
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    if request.accepted_renderer.format == 'html':
                        messages.error(request, 'Invalid username or password')
                        return Response({}, template_name='tasks/auth.html')
                    return Response({
                        'error': 'Invalid credentials'
                    }, status=status.HTTP_401_UNAUTHORIZED)

            elif action_type == 'register':
                username = request.POST.get(
                    'username') or request.data.get('username')
                password = request.POST.get(
                    'password') or request.data.get('password')
                email = request.POST.get(
                    'email', '') or request.data.get('email', '')

                if User.objects.filter(username=username).exists():
                    if request.accepted_renderer.format == 'html':
                        messages.error(request, 'Username already exists')
                        return Response({}, template_name='tasks/auth.html')
                    return Response({
                        'error': 'Username already exists'
                    }, status=status.HTTP_400_BAD_REQUEST)

                user = User.objects.create_user(
                    username=username, password=password, email=email)

                if request.accepted_renderer.format == 'html':
                    login(request, user)
                    return redirect('task-dashboard')

                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Registration successful',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_staff': user.is_staff
                    },
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token)
                    }
                }, status=status.HTTP_201_CREATED)

        return Response({}, template_name='tasks/auth.html')

    @action(detail=False, methods=['post'], url_path='logout')
    def logout_action(self, request):
        if request.accepted_renderer.format == 'html':
            logout(request)
            return redirect('auth-auth-page')

        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass

        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh_token(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({
                'error': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                'access': str(refresh.access_token)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Invalid or expired refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['title', 'description', 'project__name']
    ordering_fields = ['created_at', 'updated_at',
                       'due_date', 'status', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        return Task.objects.all().select_related('project', 'assigned_to', 'created_by')

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_template_names(self):
        if self.action == 'dashboard':
            return ['tasks/dashboard.html']
        elif self.action in ['update', 'partial_update', 'retrieve']:
            return ['tasks/task_edit.html']
        return ['tasks/dashboard.html']

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        if not request.user.is_authenticated:
            if request.accepted_renderer.format == 'html':
                return redirect('auth-auth-page')
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        tasks = self.get_queryset()
        project_id = request.GET.get('project')

        if project_id:
            tasks = tasks.filter(project_id=project_id)

        tasks = self.filter_queryset(tasks)
        projects = Project.objects.all()

        if request.accepted_renderer.format == 'html':
            return Response({
                'tasks': tasks,
                'projects': projects,
                'selected_project': project_id
            })

        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.accepted_renderer.format == 'html':
                return redirect('auth-auth-page')
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        queryset = self.get_queryset()
        project_id = request.GET.get('project')

        if project_id:
            queryset = queryset.filter(project_id=project_id)

        queryset = self.filter_queryset(queryset)

        if request.accepted_renderer.format == 'html':
            projects = Project.objects.all()
            return Response({
                'tasks': queryset,
                'projects': projects,
                'selected_project': project_id
            }, template_name='tasks/dashboard.html')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.accepted_renderer.format == 'html':
                return redirect('auth-auth-page')
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        instance = self.get_object()

        if request.accepted_renderer.format == 'html':
            projects = Project.objects.all()
            return Response({
                'task': instance,
                'projects': projects
            })

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.accepted_renderer.format == 'html':
                return redirect('auth-auth-page')
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)

            if request.accepted_renderer.format == 'html':
                return redirect('task-dashboard')

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.accepted_renderer.format == 'html':
            projects = Project.objects.all()
            return Response({
                'projects': projects,
                'errors': serializer.errors
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.accepted_renderer.format == 'html':
                return redirect('auth-auth-page')
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)

        if serializer.is_valid():
            self.perform_update(serializer)

            if request.accepted_renderer.format == 'html':
                return redirect('task-dashboard')

            return Response(serializer.data)

        if request.accepted_renderer.format == 'html':
            projects = Project.objects.all()
            return Response({
                'task': instance,
                'projects': projects,
                'errors': serializer.errors
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.accepted_renderer.format == 'html':
                return redirect('auth-auth-page')
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        instance = self.get_object()
        self.perform_destroy(instance)

        if request.accepted_renderer.format == 'html':
            return redirect('task-dashboard')

        return Response(status=status.HTTP_204_NO_CONTENT)
    

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProjectFilter
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        return Project.objects.all().select_related('created_by')

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_template_names(self):
        return ['tasks/project_list.html']

    def list(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.accepted_renderer.format == 'html':
                return redirect('auth-auth-page')
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        queryset = self.filter_queryset(self.get_queryset())

        if request.accepted_renderer.format == 'html':
            return Response({
                'projects': queryset
            }, template_name='tasks/project_list.html')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.accepted_renderer.format == 'html':
                return redirect('auth-auth-page')
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        instance = self.get_object()

        if request.accepted_renderer.format == 'html':
            return Response({'project': instance})

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.accepted_renderer.format == 'html':
                return redirect('auth-auth-page')
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)

            if request.accepted_renderer.format == 'html':
                return redirect('project-list')

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.accepted_renderer.format == 'html':
            return Response({'errors': serializer.errors})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.accepted_renderer.format == 'html':
                return redirect('auth-auth-page')
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)

        if serializer.is_valid():
            self.perform_update(serializer)

            if request.accepted_renderer.format == 'html':
                return redirect('project-list')

            return Response(serializer.data)

        if request.accepted_renderer.format == 'html':
            return Response({
                'project': instance,
                'errors': serializer.errors
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.accepted_renderer.format == 'html':
                return redirect('auth-auth-page')
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        instance = self.get_object()
        self.perform_destroy(instance)

        if request.accepted_renderer.format == 'html':
            return redirect('project-list')

        return Response(status=status.HTTP_204_NO_CONTENT)
