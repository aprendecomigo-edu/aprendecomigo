from datetime import datetime, timedelta

from django.utils import timezone
from knox.auth import TokenAuthentication
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Task, TaskComment
from .serializers import (
    TaskCommentSerializer,
    TaskCreateSerializer,
    TaskSerializer,
    TaskSummarySerializer,
    TaskUpdateSerializer,
)


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for Task model"""

    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter tasks by current user"""
        return Task.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "create":
            return TaskCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return TaskUpdateSerializer
        return TaskSerializer

    def perform_create(self, serializer):
        """Create task with current user"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get task summary statistics"""
        queryset = self.get_queryset()
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        week_end = today_start + timedelta(days=7)

        summary_data = {
            "total_tasks": queryset.count(),
            "pending_tasks": queryset.filter(status="pending").count(),
            "in_progress_tasks": queryset.filter(status="in_progress").count(),
            "completed_tasks": queryset.filter(status="completed").count(),
            "overdue_tasks": queryset.filter(due_date__lt=now, status__in=["pending", "in_progress"]).count(),
            "urgent_tasks": queryset.filter(is_urgent=True, status__in=["pending", "in_progress"]).count(),
            "tasks_due_today": queryset.filter(
                due_date__gte=today_start,
                due_date__lt=today_end,
                status__in=["pending", "in_progress"],
            ).count(),
            "tasks_due_this_week": queryset.filter(
                due_date__gte=today_start,
                due_date__lt=week_end,
                status__in=["pending", "in_progress"],
            ).count(),
        }

        serializer = TaskSummarySerializer(summary_data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def pending(self, request):
        """Get pending tasks"""
        queryset = self.get_queryset().filter(status="pending")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        """Get overdue tasks"""
        now = timezone.now()
        queryset = self.get_queryset().filter(due_date__lt=now, status__in=["pending", "in_progress"])
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def due_today(self, request):
        """Get tasks due today"""
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        queryset = self.get_queryset().filter(
            due_date__gte=today_start, due_date__lt=today_end, status__in=["pending", "in_progress"]
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def calendar(self, request):
        """Get tasks for calendar view"""
        # Get date range from query parameters
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        queryset = self.get_queryset().filter(due_date__isnull=False)

        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                queryset = queryset.filter(due_date__gte=start_date)
            except ValueError:
                pass

        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                queryset = queryset.filter(due_date__lte=end_date)
            except ValueError:
                pass

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark task as completed"""
        task = self.get_object()
        task.status = "completed"
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        """Reopen a completed task"""
        task = self.get_object()
        task.status = "pending"
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)


class TaskCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for TaskComment model"""

    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskCommentSerializer

    def get_queryset(self):
        """Filter comments by task and user access"""
        task_id = self.kwargs.get("task_pk")
        if task_id:
            # Ensure user can only see comments for their own tasks
            task = Task.objects.filter(id=task_id, user=self.request.user).first()
            if task:
                return TaskComment.objects.filter(task=task)
        return TaskComment.objects.none()

    def get_serializer_context(self):
        """Add task to serializer context"""
        context = super().get_serializer_context()
        task_id = self.kwargs.get("task_pk")
        if task_id:
            context["task"] = Task.objects.filter(id=task_id, user=self.request.user).first()
        return context

    def perform_create(self, serializer):
        """Create comment with current user and task"""
        task_id = self.kwargs.get("task_pk")
        task = Task.objects.filter(id=task_id, user=self.request.user).first()
        if task:
            serializer.save(user=self.request.user, task=task)
        else:
            raise serializers.ValidationError("Task not found")
