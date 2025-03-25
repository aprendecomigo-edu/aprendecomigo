from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Subject(models.Model):
    """Subject model for different courses and subjects."""
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('subject')
        verbose_name_plural = _('subjects')


class ClassType(models.Model):
    """Class type model for different types of classes."""
    name = models.CharField(_('name'), max_length=100)
    group_class = models.BooleanField(_('group class'), default=False)
    default_duration = models.PositiveIntegerField(_('default duration (minutes)'), default=60)
    description = models.TextField(_('description'), blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('class type')
        verbose_name_plural = _('class types')


class ClassSession(models.Model):
    """Class session model for scheduling classes."""
    STATUS_CHOICES = (
        ('scheduled', _('Scheduled')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('rescheduled', _('Rescheduled')),
    )
    
    title = models.CharField(_('title'), max_length=255)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='teaching_sessions',
        verbose_name=_('teacher')
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='learning_sessions',
        verbose_name=_('students')
    )
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE,
        verbose_name=_('subject')
    )
    class_type = models.ForeignKey(
        ClassType, 
        on_delete=models.CASCADE,
        verbose_name=_('class type')
    )
    start_time = models.DateTimeField(_('start time'))
    end_time = models.DateTimeField(_('end time'))
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='scheduled')
    google_calendar_id = models.CharField(_('Google Calendar ID'), max_length=255, blank=True, null=True)
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _('class session')
        verbose_name_plural = _('class sessions')
        ordering = ['-start_time']
