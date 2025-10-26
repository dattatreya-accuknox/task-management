from django_filters import rest_framework as filters
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Task, Project


class TaskFilter(filters.FilterSet):   
    status = filters.ChoiceFilter(
        field_name='status',
        choices=Task.StatusChoices.choices,
        lookup_expr='iexact'
    )
    
    project_name = filters.CharFilter(
        field_name='project__name',
        lookup_expr='icontains'
    )

    project = filters.NumberFilter(
        field_name='project__id',
        lookup_expr='exact'
    )

    
    assigned_to = filters.NumberFilter(
        field_name='assigned_to__id',
        lookup_expr='exact'
    )

    created_by = filters.NumberFilter(
        field_name='created_by__id',
        lookup_expr='exact'
    )

    
    due_date_after = filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='gte'
    )

    due_date_before = filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='lte'
    )

    due_date_date = filters.DateFilter(
        field_name='due_date__date',
        lookup_expr='exact'
    )

    
    due_date_upcoming = filters.NumberFilter(
        method='filter_upcoming_due_date'
    )

    
    is_overdue = filters.BooleanFilter(
        method='filter_overdue'
    )

    
    created_after = filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )

    created_before = filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )

    created_date = filters.DateFilter(
        field_name='created_at__date',
        lookup_expr='exact'
    )

    
    search = filters.CharFilter(
        method='filter_search'
    )

    class Meta:
        model = Task
        fields = {
            'title': ['exact', 'icontains'],
            'status': ['exact'],
        }

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value)
        )

    def filter_upcoming_due_date(self, queryset, name, value):
        if value:
            now = timezone.now()
            end_date = now + timedelta(days=int(value))
            return queryset.filter(
                due_date__gte=now,
                due_date__lte=end_date
            ).exclude(status=Task.StatusChoices.COMPLETED)
        return queryset

    def filter_overdue(self, queryset, name, value):
        if value:
            return queryset.filter(
                due_date__lt=timezone.now()
            ).exclude(status=Task.StatusChoices.COMPLETED)
        return queryset


class ProjectFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='icontains'
    )

    created_by = filters.NumberFilter(
        field_name='created_by__id',
        lookup_expr='exact'
    )

    created_after = filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )

    created_before = filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )

    class Meta:
        model = Project
        fields = ['name', 'created_by']
        

# class IsOwnerOrAdminFilter(filters.BaseFilterBackend):
#     def filter_queryset(self, request, queryset, view):
#         if request.user.is_staff:
#             return queryset
#         return queryset.filter(
#             Q(created_by=request.user) |
#             Q(assigned_to=request.user)
#         )
