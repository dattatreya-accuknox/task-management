from rest_framework import serializers
from .models import Task, Project


class TaskSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    project_name = serializers.ReadOnlyField(source='project.name')
    assigned_to_username = serializers.ReadOnlyField(source='assigned_to.username')
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'project', 'is_overdue', 'created_by',
                  'assigned_to_username','assigned_to', 'due_date', 'project_name', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'is_overdue']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ProjectSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    created_by = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = Project
        fields = ['id', 'name', 'description','created_by',
                  'created_at', 'updated_at', 'tasks']
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
