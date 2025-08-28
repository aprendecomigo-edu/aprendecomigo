from django.urls import path

from .views import TaskDetailView, TaskListView, TaskSummaryView

app_name = "tasks"

urlpatterns = [
    # Main tasks page
    path("", TaskListView.as_view(), name="task_list"),
    
    # Task detail/edit
    path("<int:task_id>/", TaskDetailView.as_view(), name="task_detail"),
    
    # Task summary widget (for dashboard integration)
    path("summary/", TaskSummaryView.as_view(), name="task_summary"),
]
