from typing import ClassVar

from django.utils import timezone
from rest_framework import serializers

from .models import Task, TaskComment


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model"""

    is_overdue = serializers.ReadOnlyField()
    days_until_due = serializers.ReadOnlyField()

    class Meta:
        model = Task
        fields: ClassVar = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "task_type",
            "due_date",
            "completed_at",
            "created_at",
            "updated_at",
            "is_urgent",
            "is_system_generated",
            "is_overdue",
            "days_until_due",
        ]
        read_only_fields: ClassVar = ["id", "created_at", "updated_at", "completed_at", "is_system_generated"]

    def validate_due_date(self, value):
        """Validate that due date is not in the past"""
        if value and value < timezone.now():
            raise serializers.ValidationError("Due date cannot be in the past")
        return value


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks"""

    class Meta:
        model = Task
        fields: ClassVar = ["title", "description", "priority", "task_type", "due_date", "is_urgent"]

    def validate_due_date(self, value):
        """Validate that due date is not in the past"""
        if value and value < timezone.now():
            raise serializers.ValidationError("Due date cannot be in the past")
        return value

    def create(self, validated_data):
        """Create task with current user"""
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tasks"""

    class Meta:
        model = Task
        fields: ClassVar = [
            "title",
            "description",
            "status",
            "priority",
            "task_type",
            "due_date",
            "is_urgent",
        ]

    def validate_due_date(self, value):
        """Validate that due date is not in the past"""
        if value and value < timezone.now():
            raise serializers.ValidationError("Due date cannot be in the past")
        return value


class TaskCommentSerializer(serializers.ModelSerializer):
    """Serializer for TaskComment model"""

    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = TaskComment
        fields: ClassVar = ["id", "comment", "created_at", "user_name"]
        read_only_fields: ClassVar = ["id", "created_at", "user_name"]

    def create(self, validated_data):
        """Create comment with current user and task"""
        validated_data["user"] = self.context["request"].user
        validated_data["task"] = self.context["task"]
        return super().create(validated_data)


class TaskSummarySerializer(serializers.Serializer):
    """Serializer for task summary statistics"""

    total_tasks = serializers.IntegerField()
    pending_tasks = serializers.IntegerField()
    in_progress_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    urgent_tasks = serializers.IntegerField()
    tasks_due_today = serializers.IntegerField()
    tasks_due_this_week = serializers.IntegerField()
