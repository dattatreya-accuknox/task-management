from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Task
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Task)
def capture_previous_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            previous = Task.objects.get(pk=instance.pk)
            instance._previous_status = previous.status
        except Task.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None

@receiver(post_save, sender=Task)
def notify_on_task_status_change(sender, instance, created, **kwargs):
    if created:
        notify_task_created(instance)
        logger.info(f"Task created: {instance.title} (ID: {instance.id})")
    else:
        previous_status = getattr(instance, '_previous_status', None)
        if previous_status and previous_status != instance.status:
            notify_status_changed(instance, previous_status, instance.status)
            logger.info(
                f"Task status changed: {instance.title} - {previous_status} → {instance.status}"
            )


def notify_task_created(task):
    if task.assigned_to and task.assigned_to.email:
        subject = f"New Task Assigned: {task.title}"
        message = f"""
                Hi {task.assigned_to.username},

                A new task has been assigned to you:

                Task: {task.title}
                Description: {task.description}
                Project: {task.project.name if task.project else 'N/A'}
                Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'N/A'}
                Status: {task.get_status_display()}
                Created By: {task.created_by.username if task.created_by else 'Unknown'}

                Please log in to view more details.

                Best regards,
                Task Management System
        """

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[task.assigned_to.email],
                fail_silently=False,
            )
            logger.info(
                f"Email sent to {task.assigned_to.email} for new task {task.id}")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
    else:
        logger.warning(f"Task {task.id} has no assigned user or email")


def notify_status_changed(task, old_status, new_status):
    recipients = []
    if task.assigned_to and task.assigned_to.email:
        recipients.append(task.assigned_to.email)

    if task.created_by and task.created_by.email and task.created_by != task.assigned_to:
        recipients.append(task.created_by.email)

    if not recipients:
        logger.warning(
            f"No recipients for task {task.id} status change notification")
        return

    subject = f"Task Status Updated: {task.title}"
    message = f"""
            Hi,

            The status of task "{task.title}" has been updated:

            Previous Status: {dict(Task.StatusChoices.choices).get(old_status, old_status)}
            New Status: {dict(Task.StatusChoices.choices).get(new_status, new_status)}

            Task Details:
            - Project: {task.project.name if task.project else 'N/A'}
            - Assigned To: {task.assigned_to.username if task.assigned_to else 'Unassigned'}
            - Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'N/A'}

            Description: {task.description}

            Please log in to view more details.

            Best regards,
            Task Management System
    """

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
        logger.info(
            f"Status change email sent to {recipients} for task {task.id}")
    except Exception as e:
        logger.error(f"Failed to send status change email: {str(e)}")


