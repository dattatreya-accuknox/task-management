from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from .models import Task
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_task_reminder_email(task_id):
    try:
        task = Task.objects.select_related(
            'assigned_to', 'project').get(id=task_id)
    except Task.DoesNotExist:
        logger.warning(f'Task {task_id} no longer exists, skipping reminder')
        return f'Task {task_id} not found'

    if not task.assigned_to or not task.assigned_to.email:
        logger.warning(f'Task {task_id} has no assigned user or email')
        return f'No email recipient for task {task_id}'

    subject = f'Reminder: Upcoming Deadline for Task {task.title}'

    if task.due_date:
        time_remaining = task.due_date - timezone.now()
        days_remaining = time_remaining.days
        hours_remaining = time_remaining.seconds // 3600
        minutes_remaining = (time_remaining.seconds % 3600) // 60
        seconds_remaining = time_remaining.seconds % 60

        if days_remaining > 0:
            time_str = f'{days_remaining} days'
        else:
            time_str = f'{hours_remaining}h {minutes_remaining}m {seconds_remaining}s'
    else:
        time_str = 'Not set'

    message = f'''
                Hi {task.assigned_to.username},

                This is a reminder about an upcoming task deadline:

                Task: {task.title}
                Description: {task.description}
                Project: {task.project.name if task.project else 'N/A'}
                Current Status: {task.get_status_display()}
                Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'Not set'}
                Time Remaining: {time_str}

                Please ensure you complete this task before the deadline.
                Log in to view more details and update the task status.

                Best regards,
                Task Management System
                '''

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[task.assigned_to.email],
            fail_silently=False,
        )
        logger.info(
            f'Reminder email sent for task {task_id} to {task.assigned_to.email}')
        return f'Reminder sent for task {task_id}'
    except Exception as e:
        logger.error(f'Error sending reminder for task {task_id}: {str(e)}')
        raise


@shared_task
def check_upcoming_deadlines():
    logger.info('Running check_upcoming_deadlines task')

    now = timezone.now()
    tomorrow = now + timedelta(hours=24)

    upcoming_tasks = Task.objects.filter(
        due_date__gte=now,
        due_date__lte=tomorrow,
        status__in=[Task.StatusChoices.PENDING, Task.StatusChoices.IN_PROGRESS]
    ).select_related('assigned_to', 'project')

    count = 0
    for task in upcoming_tasks:
        if task.assigned_to and task.assigned_to.email:
            send_task_reminder_email.delay(task.id)
            count += 1

    logger.info(f'Sent {count} deadline reminder emails')
    return f'Checked and sent {count} reminders'


@shared_task
def check_overdue_tasks():
    logger.info('Running check_overdue_tasks task')

    now = timezone.now()
    overdue_tasks = Task.objects.filter(
        due_date__lt=now,
        status__in=[Task.StatusChoices.PENDING, Task.StatusChoices.IN_PROGRESS]
    ).select_related('assigned_to', 'created_by', 'project')

    count = 0
    for task in overdue_tasks:
        recipients = []
        if task.assigned_to and task.assigned_to.email:
            recipients.append(task.assigned_to.email)
        if task.created_by and task.created_by.email and task.created_by != task.assigned_to:
            recipients.append(task.created_by.email)

        if recipients:
            send_overdue_notification.delay(task.id, recipients)
            count += 1

    logger.info(f'Sent {count} overdue task notifications')
    return f'Checked and sent {count} overdue notifications'


@shared_task
def send_overdue_notification(task_id, recipients):
    try:
        task = Task.objects.select_related(
            'assigned_to', 'project').get(id=task_id)
    except Task.DoesNotExist:
        logger.warning(
            f'Task {task_id} no longer exists, skipping overdue notification')
        return f'Task {task_id} not found'

    overdue_time = timezone.now() - task.due_date
    days_overdue = overdue_time.days

    subject = f'OVERDUE: Task {task.title} - Action Required'

    message = f'''
            URGENT: This task is now overdue!

            Task: {task.title}
            Description: {task.description}
            Project: {task.project.name if task.project else 'N/A'}
            Status: {task.get_status_display()}
            Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M')}
            Days Overdue: {days_overdue}
            Assigned To: {task.assigned_to.username if task.assigned_to else 'Unassigned'}

            Please take immediate action to complete or update this task.

            Best regards,
            Task Management System
            '''

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
        logger.info(f'Overdue notification sent for task {task_id}')
        return f'Overdue notification sent for task {task_id}'
    except Exception as e:
        logger.error(f'Error sending overdue notification: {str(e)}')
        raise


@shared_task
def send_daily_task_summary():
    logger.info('Running send_daily_task_summary task')

    users = User.objects.filter(
        is_active=True, email__isnull=False).exclude(email='')
    count = 0

    for user in users:
        pending_tasks = Task.objects.filter(
            assigned_to=user,
            status=Task.StatusChoices.PENDING
        ).count()

        in_progress_tasks = Task.objects.filter(
            assigned_to=user,
            status=Task.StatusChoices.IN_PROGRESS
        ).count()

        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        due_today = Task.objects.filter(
            assigned_to=user,
            due_date__gte=today_start,
            due_date__lt=today_end,
            status__in=[Task.StatusChoices.PENDING,
                        Task.StatusChoices.IN_PROGRESS]
        )

        if pending_tasks > 0 or in_progress_tasks > 0:
            subject = f'Daily Task Summary - {timezone.now().strftime("%Y-%m-%d")}'

            due_today_list = '\n'.join([
                f' - {task.title} (Due: {task.due_date.strftime("%H:%M")})'
                for task in due_today
            ])

            message = f'''
                Hi {user.username},

                Here's your daily task summary:

                Pending Tasks: {pending_tasks}
                In Progress Tasks: {in_progress_tasks}

                Tasks Due Today:
                {due_today_list if due_today_list else 'None'}

                Log in to manage your tasks.

                Best regards,
                Task Management System
            '''

            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                count += 1
            except Exception as e:
                logger.error(
                    f'Error sending daily summary to {user.email}: {str(e)}')

    logger.info(f'Sent daily summary to {count} users')
    return f'Sent daily summary to {count} users'


@shared_task
def schedule_task_reminder(task_id, hours_before_deadline=24):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        logger.info(
            f'Task {task_id} no longer exists, skipping reminder scheduling')
        return 'Task not found'

    if not task.due_date:
        logger.info(
            f'Task {task_id} has no due date, skipping reminder scheduling')
        return 'No due date set'

    reminder_time = task.due_date - timedelta(hours=hours_before_deadline)
    now = timezone.now()

    if reminder_time > now:
        send_task_reminder_email.apply_async(args=[task_id], eta=reminder_time)
        logger.info(
            f'Reminder scheduled for task {task_id} at {reminder_time}')
        return f'Reminder scheduled for {reminder_time}'
    else:
        logger.info(
            f'Deadline too soon for task {task_id}, sending immediate reminder')
        send_task_reminder_email.delay(task_id)
        return 'Immediate reminder sent'
