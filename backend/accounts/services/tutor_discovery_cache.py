"""
Cache management service for tutor discovery.

Handles cache warming, invalidation, and optimization strategies 
for the public tutor discovery API.
"""

import logging
from typing import List, Optional
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

from accounts.models import TeacherProfile, TeacherCourse, SchoolMembership

logger = logging.getLogger(__name__)


class TutorDiscoveryCacheService:
    """Service for managing tutor discovery cache."""
    
    CACHE_PREFIX = 'tutor_discovery'
    CACHE_TIMEOUT = 300  # 5 minutes
    POPULAR_QUERIES_CACHE_KEY = 'tutor_discovery_popular_queries'
    
    @classmethod
    def get_cache_key_pattern(cls, filters=None, pagination=None, ordering=None):
        """Generate cache key pattern for cache invalidation."""
        return f"{cls.CACHE_PREFIX}_*"
    
    @classmethod
    def invalidate_all_tutor_discovery_cache(cls):
        """Invalidate all tutor discovery cache entries."""
        try:
            # In production, you would use a more sophisticated approach
            # like storing cache keys in a set or using cache tagging
            pattern = cls.get_cache_key_pattern()
            
            # For now, we'll clear specific known patterns
            # In a real implementation, you'd track all cache keys
            common_keys = [
                'tutor_discovery_limit_20_offset_0_order_-completion_score',
                'tutor_discovery_ordering_rate',
                'tutor_discovery_ordering_-rate',
                'tutor_discovery_ordering_completion_score',
                'tutor_discovery_ordering_-completion_score',
            ]
            
            for key in common_keys:
                cache.delete(key)
            
            # Also clear popular queries cache
            cache.delete(cls.POPULAR_QUERIES_CACHE_KEY)
            
            logger.info("Invalidated tutor discovery cache")
            
        except Exception as e:
            logger.error(f"Error invalidating tutor discovery cache: {str(e)}")
    
    @classmethod
    def warm_popular_queries_cache(cls):
        """Warm cache for popular query patterns."""
        try:
            from accounts.views import TutorDiscoveryAPIView
            from rest_framework.test import APIRequestFactory
            
            factory = APIRequestFactory()
            view = TutorDiscoveryAPIView()
            
            # Popular query patterns to warm
            popular_patterns = [
                {},  # Default query
                {'ordering': '-completion_score'},
                {'ordering': 'rate'},
                {'ordering': '-rate'},
                {'rate_min': '20', 'rate_max': '50'},
                {'subjects': 'Mathematics'},
                {'subjects': 'Physics'},
                {'education_level': '10'},
                {'education_level': '11'},
                {'education_level': '12'},
            ]
            
            for params in popular_patterns:
                try:
                    request = factory.get('/api/accounts/tutors/discover/', params)
                    
                    # Parse parameters using the view's methods
                    filters = view._parse_filters(request.query_params)
                    pagination = view._parse_pagination(request.query_params)
                    ordering = view._parse_ordering(request.query_params)
                    
                    # Generate cache key
                    cache_key = view._generate_cache_key(filters, pagination, ordering)
                    
                    # Only warm if not already cached
                    if not cache.get(cache_key):
                        # Build and execute query
                        queryset = view._build_tutors_queryset(filters, ordering)
                        total_count = queryset.count()
                        queryset = queryset[pagination['offset']:pagination['offset'] + pagination['limit']]
                        
                        # Serialize data
                        tutors_data = view._serialize_public_tutors(queryset, request)
                        
                        result = {
                            'results': tutors_data,
                            'count': len(tutors_data),
                            'total': total_count,
                            'next': view._get_next_url(request, pagination, total_count),
                            'previous': view._get_previous_url(request, pagination)
                        }
                        
                        # Cache the result
                        cache.set(cache_key, result, timeout=cls.CACHE_TIMEOUT)
                        
                        logger.debug(f"Warmed cache for pattern: {params}")
                        
                except Exception as e:
                    logger.warning(f"Could not warm cache for pattern {params}: {str(e)}")
                    continue
            
            logger.info("Completed cache warming for popular tutor discovery queries")
            
        except Exception as e:
            logger.error(f"Error warming tutor discovery cache: {str(e)}")
    
    @classmethod
    def track_popular_query(cls, filters, pagination, ordering):
        """Track popular queries for future cache warming."""
        try:
            # Create a simplified key for tracking
            query_signature = {
                'subjects': filters.get('subjects', [])[:2] if filters.get('subjects') else [],  # First 2 subjects
                'rate_min': filters.get('rate_min'),
                'rate_max': filters.get('rate_max'),
                'education_level': filters.get('education_level'),
                'educational_system': filters.get('educational_system'),
                'search': bool(filters.get('search')),  # Just track if search was used
                'ordering': ordering,
                'limit': pagination['limit']
            }
            
            # Get current popular queries
            popular_queries = cache.get(cls.POPULAR_QUERIES_CACHE_KEY, {})
            
            # Convert dict to hashable key
            query_key = str(sorted(query_signature.items()))
            
            # Increment counter
            popular_queries[query_key] = popular_queries.get(query_key, 0) + 1
            
            # Keep only top 20 most popular queries
            if len(popular_queries) > 20:
                # Sort by popularity and keep top 20
                sorted_queries = sorted(popular_queries.items(), key=lambda x: x[1], reverse=True)
                popular_queries = dict(sorted_queries[:20])
            
            # Update cache
            cache.set(cls.POPULAR_QUERIES_CACHE_KEY, popular_queries, timeout=86400)  # 24 hours
            
        except Exception as e:
            logger.warning(f"Error tracking popular query: {str(e)}")


# Signal handlers for cache invalidation
@receiver(post_save, sender=TeacherProfile)
def invalidate_cache_on_teacher_profile_change(sender, instance, **kwargs):
    """Invalidate tutor discovery cache when teacher profile changes."""
    # Only invalidate if this affects discovery (complete profiles)
    if instance.is_profile_complete:
        TutorDiscoveryCacheService.invalidate_all_tutor_discovery_cache()


@receiver(post_delete, sender=TeacherProfile)
def invalidate_cache_on_teacher_profile_delete(sender, instance, **kwargs):
    """Invalidate tutor discovery cache when teacher profile is deleted."""
    TutorDiscoveryCacheService.invalidate_all_tutor_discovery_cache()


@receiver(post_save, sender=TeacherCourse)
def invalidate_cache_on_teacher_course_change(sender, instance, **kwargs):
    """Invalidate tutor discovery cache when teacher course changes."""
    # Only invalidate if the teacher has a complete profile
    if hasattr(instance.teacher, 'is_profile_complete') and instance.teacher.is_profile_complete:
        TutorDiscoveryCacheService.invalidate_all_tutor_discovery_cache()


@receiver(post_delete, sender=TeacherCourse)
def invalidate_cache_on_teacher_course_delete(sender, instance, **kwargs):
    """Invalidate tutor discovery cache when teacher course is deleted."""
    # Only invalidate if the teacher has a complete profile
    if hasattr(instance.teacher, 'is_profile_complete') and instance.teacher.is_profile_complete:
        TutorDiscoveryCacheService.invalidate_all_tutor_discovery_cache()


@receiver(post_save, sender=SchoolMembership)
def invalidate_cache_on_school_membership_change(sender, instance, **kwargs):
    """Invalidate tutor discovery cache when school membership changes."""
    # Check if this affects a teacher with a complete profile
    if (hasattr(instance.user, 'teacher_profile') and 
        instance.user.teacher_profile.is_profile_complete and
        instance.role in ['teacher', 'school_owner']):
        TutorDiscoveryCacheService.invalidate_all_tutor_discovery_cache()


@receiver(post_delete, sender=SchoolMembership)
def invalidate_cache_on_school_membership_delete(sender, instance, **kwargs):
    """Invalidate tutor discovery cache when school membership is deleted."""
    # Check if this affects a teacher with a complete profile
    if (hasattr(instance.user, 'teacher_profile') and 
        instance.user.teacher_profile.is_profile_complete and
        instance.role in ['teacher', 'school_owner']):
        TutorDiscoveryCacheService.invalidate_all_tutor_discovery_cache()