"""
Task management views following Django + HTMX patterns for PWA migration
"""
from datetime import datetime, timedelta
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View

from .models import Task

User = get_user_model()
logger = logging.getLogger('tasks.views')


class TaskListView(LoginRequiredMixin, View):
    """Main tasks page with filtering and HTMX support"""

    def get(self, request):
        """Render tasks page with server-side data"""

        # Handle HTMX partial requests
        if request.headers.get('HX-Request'):
            filter_type = request.GET.get('filter', 'all')
            return self._handle_task_filter(request, filter_type)

        # Get initial tasks data
        tasks = self._get_user_tasks(request.user)
        summary = self._get_task_summary(request.user)

        # Get filter from query params
        filter_type = request.GET.get('filter', 'all')
        filtered_tasks = self._filter_tasks(tasks, filter_type)

        return render(request, 'tasks/task_list.html', {
            'title': 'Tasks - Aprende Comigo',
            'user': request.user,
            'active_section': 'tasks',
            'tasks': filtered_tasks,
            'summary': summary,
            'current_filter': filter_type,
        })

    def post(self, request):
        """Handle task actions via HTMX"""
        action = request.POST.get('action')

        if action == 'create_task':
            return self._handle_create_task(request)
        elif action == 'complete_task':
            return self._handle_complete_task(request)
        elif action == 'reopen_task':
            return self._handle_reopen_task(request)
        elif action == 'delete_task':
            return self._handle_delete_task(request)
        elif action == 'filter_tasks':
            filter_type = request.POST.get('filter', 'all')
            return self._handle_task_filter(request, filter_type)
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)

    def _get_user_tasks(self, user):
        """Get all tasks for the user"""
        return Task.objects.filter(user=user).order_by('-priority', 'due_date', '-created_at')

    def _filter_tasks(self, tasks, filter_type):
        """Filter tasks based on filter type"""
        now = timezone.now()

        if filter_type == 'pending':
            return tasks.filter(status='pending')
        elif filter_type == 'in_progress':
            return tasks.filter(status='in_progress')
        elif filter_type == 'completed':
            return tasks.filter(status='completed')
        elif filter_type == 'overdue':
            return tasks.filter(
                due_date__lt=now,
                status__in=['pending', 'in_progress']
            )
        elif filter_type == 'due_today':
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            return tasks.filter(
                due_date__gte=today_start,
                due_date__lt=today_end,
                status__in=['pending', 'in_progress']
            )
        elif filter_type == 'urgent':
            return tasks.filter(is_urgent=True, status__in=['pending', 'in_progress'])
        else:  # 'all'
            return tasks

    def _get_task_summary(self, user):
        """Get task summary statistics"""
        tasks = self._get_user_tasks(user)
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        week_end = today_start + timedelta(days=7)

        return {
            'total_tasks': tasks.count(),
            'pending_tasks': tasks.filter(status='pending').count(),
            'in_progress_tasks': tasks.filter(status='in_progress').count(),
            'completed_tasks': tasks.filter(status='completed').count(),
            'overdue_tasks': tasks.filter(
                due_date__lt=now,
                status__in=['pending', 'in_progress']
            ).count(),
            'urgent_tasks': tasks.filter(
                is_urgent=True,
                status__in=['pending', 'in_progress']
            ).count(),
            'tasks_due_today': tasks.filter(
                due_date__gte=today_start,
                due_date__lt=today_end,
                status__in=['pending', 'in_progress']
            ).count(),
            'tasks_due_this_week': tasks.filter(
                due_date__gte=today_start,
                due_date__lt=week_end,
                status__in=['pending', 'in_progress']
            ).count(),
        }

    def _handle_task_filter(self, request, filter_type):
        """Handle task filtering via HTMX"""
        tasks = self._get_user_tasks(request.user)
        filtered_tasks = self._filter_tasks(tasks, filter_type)
        summary = self._get_task_summary(request.user)

        return render(request, 'tasks/partials/task_list_content.html', {
            'tasks': filtered_tasks,
            'summary': summary,
            'current_filter': filter_type,
        })

    def _handle_create_task(self, request):
        """Handle creating a new task"""
        try:
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            priority = request.POST.get('priority', 'medium')
            task_type = request.POST.get('task_type', 'personal')
            due_date = request.POST.get('due_date')
            is_urgent = request.POST.get('is_urgent') == 'on'

            if not title:
                return render(request, 'tasks/partials/error_message.html', {
                    'error': 'Task title is required'
                })

            # Validate due date if provided
            parsed_due_date = None
            if due_date:
                try:
                    parsed_due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    if parsed_due_date < timezone.now():
                        return render(request, 'tasks/partials/error_message.html', {
                            'error': 'Due date cannot be in the past'
                        })
                except ValueError:
                    return render(request, 'tasks/partials/error_message.html', {
                        'error': 'Invalid due date format'
                    })

            # Create the task
            task = Task.objects.create(
                user=request.user,
                title=title,
                description=description,
                priority=priority,
                task_type=task_type,
                due_date=parsed_due_date,
                is_urgent=is_urgent
            )

            # Return the new task item and trigger list refresh
            response = render(request, 'tasks/partials/task_item.html', {
                'task': task
            })
            response['HX-Trigger'] = 'taskCreated'
            return response

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return render(request, 'tasks/partials/error_message.html', {
                'error': 'Failed to create task. Please try again.'
            })

    def _handle_complete_task(self, request):
        """Handle marking a task as completed"""
        try:
            task_id = request.POST.get('task_id')
            if not task_id:
                return JsonResponse({'error': 'Task ID required'}, status=400)

            task = get_object_or_404(Task, id=task_id, user=request.user)
            task.status = 'completed'
            task.save()

            # Return updated task item
            return render(request, 'tasks/partials/task_item.html', {
                'task': task
            })

        except Exception as e:
            logger.error(f"Error completing task: {e}")
            return render(request, 'tasks/partials/error_message.html', {
                'error': 'Failed to complete task'
            })

    def _handle_reopen_task(self, request):
        """Handle reopening a completed task"""
        try:
            task_id = request.POST.get('task_id')
            if not task_id:
                return JsonResponse({'error': 'Task ID required'}, status=400)

            task = get_object_or_404(Task, id=task_id, user=request.user)
            task.status = 'pending'
            task.save()

            # Return updated task item
            return render(request, 'tasks/partials/task_item.html', {
                'task': task
            })

        except Exception as e:
            logger.error(f"Error reopening task: {e}")
            return render(request, 'tasks/partials/error_message.html', {
                'error': 'Failed to reopen task'
            })

    def _handle_delete_task(self, request):
        """Handle deleting a task"""
        try:
            task_id = request.POST.get('task_id')
            if not task_id:
                return JsonResponse({'error': 'Task ID required'}, status=400)

            task = get_object_or_404(Task, id=task_id, user=request.user)
            task.delete()

            # Return empty response with trigger to remove the item
            from django.http import HttpResponse
            response = HttpResponse('')
            response['HX-Trigger'] = 'taskDeleted'
            return response

        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return render(request, 'tasks/partials/error_message.html', {
                'error': 'Failed to delete task'
            })


class TaskDetailView(LoginRequiredMixin, View):
    """Task detail/edit view"""

    def get(self, request, task_id):
        """Render task detail/edit form"""

        task = get_object_or_404(Task, id=task_id, user=request.user)

        # If this is an HTMX request for the form, return just the form
        if request.headers.get('HX-Request'):
            return render(request, 'tasks/partials/task_form.html', {
                'task': task,
                'edit_mode': True
            })

        return render(request, 'tasks/task_detail.html', {
            'title': f'Task: {task.title} - Aprende Comigo',
            'user': request.user,
            'active_section': 'tasks',
            'task': task,
        })

    def post(self, request, task_id):
        """Handle task update"""

        task = get_object_or_404(Task, id=task_id, user=request.user)

        try:
            # Update task fields
            task.title = request.POST.get('title', task.title)
            task.description = request.POST.get('description', task.description)
            task.priority = request.POST.get('priority', task.priority)
            task.task_type = request.POST.get('task_type', task.task_type)
            task.status = request.POST.get('status', task.status)
            task.is_urgent = request.POST.get('is_urgent') == 'on'

            # Handle due date
            due_date = request.POST.get('due_date')
            if due_date:
                try:
                    task.due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                except ValueError:
                    return render(request, 'tasks/partials/error_message.html', {
                        'error': 'Invalid due date format'
                    })
            else:
                task.due_date = None

            task.save()

            # Return success response
            response = render(request, 'tasks/partials/success_message.html', {
                'message': 'Task updated successfully!'
            })
            response['HX-Trigger'] = 'taskUpdated'
            return response

        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return render(request, 'tasks/partials/error_message.html', {
                'error': 'Failed to update task'
            })


class TaskSummaryView(LoginRequiredMixin, View):
    """Task summary widget for dashboard"""

    def get(self, request):
        """Return task summary partial"""

        task_list_view = TaskListView()
        summary = task_list_view._get_task_summary(request.user)

        return render(request, 'tasks/partials/task_summary.html', {
            'summary': summary
        })
