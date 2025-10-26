import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# class Comments(models.Model):
#     id = models.AutoField(primary_key=True)
#     task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='comments')
#     author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
#     content = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Comment by {self.author.username} on {self.task.title}"

#     class Meta:
#         ordering = ['-created_at']


class Task(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='tasks', null=True,blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tasks')
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
    
    @property
    def is_overdue(self):
        if self.due_date and self.status != self.StatusChoices.COMPLETED:
            if timezone.now() > self.due_date:
                return True
        return False    
            
    
class Project(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']
    
