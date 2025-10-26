from django.contrib import admin
from .models import Task, Project
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'due_date',
                    'project', 'assigned_to', 'created_by']
    list_filter = ['status', 'project', 'due_date']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'is_overdue']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    list_filter = ['created_at', 'created_by']
    search_fields = ['name', 'description']
