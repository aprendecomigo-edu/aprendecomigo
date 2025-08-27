"""
Caching utilities for education app to improve performance.
"""

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from functools import wraps
import hashlib


def cache_key_for_teacher_dashboard(teacher_id):
    """Generate cache key for teacher dashboard data."""
    return f"teacher_dashboard_{teacher_id}"


def cache_key_for_student_portal(student_id):
    """Generate cache key for student portal data."""
    return f"student_portal_{student_id}"


def cache_key_for_course_stats(course_id):
    """Generate cache key for course statistics."""
    return f"course_stats_{course_id}"


def cache_key_for_teacher_earnings(teacher_id, start_date, end_date):
    """Generate cache key for teacher earnings report."""
    date_hash = hashlib.md5(f"{start_date}_{end_date}".encode()).hexdigest()[:8]
    return f"teacher_earnings_{teacher_id}_{date_hash}"


def cache_expensive_query(timeout=60*15):
    """
    Decorator to cache expensive database queries.
    
    Args:
        timeout: Cache timeout in seconds (default: 15 minutes)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache first
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator


class CacheManager:
    """Centralized cache management for education app."""
    
    @staticmethod
    def get_teacher_dashboard_data(teacher_id):
        """Get cached teacher dashboard data."""
        return cache.get(cache_key_for_teacher_dashboard(teacher_id))
    
    @staticmethod
    def set_teacher_dashboard_data(teacher_id, data, timeout=60*15):
        """Cache teacher dashboard data."""
        cache.set(cache_key_for_teacher_dashboard(teacher_id), data, timeout)
    
    @staticmethod
    def invalidate_teacher_dashboard(teacher_id):
        """Invalidate teacher dashboard cache."""
        cache.delete(cache_key_for_teacher_dashboard(teacher_id))
    
    @staticmethod
    def get_student_portal_data(student_id):
        """Get cached student portal data."""
        return cache.get(cache_key_for_student_portal(student_id))
    
    @staticmethod
    def set_student_portal_data(student_id, data, timeout=60*15):
        """Cache student portal data."""
        cache.set(cache_key_for_student_portal(student_id), data, timeout)
    
    @staticmethod
    def invalidate_student_portal(student_id):
        """Invalidate student portal cache."""
        cache.delete(cache_key_for_student_portal(student_id))
    
    @staticmethod
    def get_course_stats(course_id):
        """Get cached course statistics."""
        return cache.get(cache_key_for_course_stats(course_id))
    
    @staticmethod
    def set_course_stats(course_id, data, timeout=60*30):
        """Cache course statistics."""
        cache.set(cache_key_for_course_stats(course_id), data, timeout)
    
    @staticmethod
    def invalidate_course_stats(course_id):
        """Invalidate course statistics cache."""
        cache.delete(cache_key_for_course_stats(course_id))
    
    @staticmethod
    def get_teacher_earnings(teacher_id, start_date, end_date):
        """Get cached teacher earnings."""
        key = cache_key_for_teacher_earnings(teacher_id, start_date, end_date)
        return cache.get(key)
    
    @staticmethod
    def set_teacher_earnings(teacher_id, start_date, end_date, data, timeout=60*60):
        """Cache teacher earnings."""
        key = cache_key_for_teacher_earnings(teacher_id, start_date, end_date)
        cache.set(key, data, timeout)
    
    @staticmethod
    def invalidate_teacher_cache(teacher_id):
        """Invalidate all cache related to a teacher."""
        # Get all keys and delete teacher-related ones
        # This is a simple approach - in production, consider using cache tags
        cache.delete(cache_key_for_teacher_dashboard(teacher_id))
        
        # For more complex invalidation, consider using cache versioning
        # or implementing cache tags with django-cache-machine


# Signal handlers to automatically invalidate cache when data changes
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Course, Enrollment, Payment, Lesson, Assignment


@receiver([post_save, post_delete], sender=Course)
def invalidate_course_cache(sender, instance, **kwargs):
    """Invalidate cache when course data changes."""
    CacheManager.invalidate_teacher_dashboard(instance.teacher.id)
    CacheManager.invalidate_course_stats(instance.id)


@receiver([post_save, post_delete], sender=Enrollment)
def invalidate_enrollment_cache(sender, instance, **kwargs):
    """Invalidate cache when enrollment data changes."""
    CacheManager.invalidate_teacher_dashboard(instance.course.teacher.id)
    CacheManager.invalidate_student_portal(instance.student.id)
    CacheManager.invalidate_course_stats(instance.course.id)


@receiver([post_save, post_delete], sender=Payment)
def invalidate_payment_cache(sender, instance, **kwargs):
    """Invalidate cache when payment data changes."""
    CacheManager.invalidate_teacher_dashboard(instance.teacher.id)
    if instance.student:
        CacheManager.invalidate_student_portal(instance.student.id)


@receiver([post_save, post_delete], sender=Lesson)
def invalidate_lesson_cache(sender, instance, **kwargs):
    """Invalidate cache when lesson data changes."""
    CacheManager.invalidate_teacher_dashboard(instance.course.teacher.id)
    CacheManager.invalidate_course_stats(instance.course.id)


@receiver([post_save, post_delete], sender=Assignment)
def invalidate_assignment_cache(sender, instance, **kwargs):
    """Invalidate cache when assignment data changes."""
    CacheManager.invalidate_teacher_dashboard(instance.course.teacher.id)
    CacheManager.invalidate_course_stats(instance.course.id)