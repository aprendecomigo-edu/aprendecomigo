"""
Django views for chat functionality (replacing DRF API).
Implements school-based user visibility similar to Slack workspaces.
"""

import json
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.models import School, SchoolMembership
from .models import Channel, Message

User = get_user_model()


def get_user_schools(user):
    """Get all schools where the user is a member."""
    if user.is_staff or user.is_superuser:
        # Staff/superuser can see all schools
        return School.objects.all()
    
    # Get schools through SchoolMembership
    school_ids = SchoolMembership.objects.filter(user=user).values_list('school_id', flat=True)
    return School.objects.filter(id__in=school_ids)


def get_school_users(schools, exclude_user=None):
    """Get all users from the given schools (teachers, students, staff)."""
    # Get all school memberships for these schools
    memberships = SchoolMembership.objects.filter(
        school__in=schools
    ).select_related('user').order_by('user__first_name', 'user__last_name')
    
    if exclude_user:
        memberships = memberships.exclude(user=exclude_user)
    
    # Extract users and add their role from the membership
    users_data = []
    for membership in memberships:
        user = membership.user
        if user.is_active:  # Only include active users
            users_data.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'role': membership.role,
                'school_id': membership.school_id,
                'school_name': membership.school.name if membership.school else ''
            })
    
    return users_data


@method_decorator(login_required, name='dispatch')
class ChatUserSearchView(View):
    """Search users within the same schools as the current user."""
    
    def get(self, request):
        query = request.GET.get('search', '').strip()
        
        if not query or len(query) < 2:
            return JsonResponse({'users': []})
        
        # Get schools where current user is a member
        user_schools = get_user_schools(request.user)
        
        if not user_schools.exists():
            return JsonResponse({'users': []})
        
        # Get all users from these schools
        school_users = get_school_users(user_schools, exclude_user=request.user)
        
        # Filter users based on search query
        filtered_users = []
        query_lower = query.lower()
        
        for user_data in school_users:
            # Search in name, email, or username
            if (query_lower in user_data['first_name'].lower() or
                query_lower in user_data['last_name'].lower() or
                query_lower in user_data['email'].lower() or
                query_lower in user_data['username'].lower()):
                filtered_users.append(user_data)
        
        # Limit results to 20
        filtered_users = filtered_users[:20]
        
        return JsonResponse({'users': filtered_users})


@method_decorator(login_required, name='dispatch')
class ChatChannelsView(View):
    """Get channels for the current user from their schools."""
    
    def get(self, request):
        # Get channels where user is a participant
        channels = Channel.objects.filter(
            participants=request.user
        ).prefetch_related(
            Prefetch('participants', queryset=User.objects.only('id', 'username', 'first_name', 'last_name', 'email')),
            Prefetch('online', queryset=User.objects.only('id', 'username', 'first_name', 'last_name'))
        ).order_by('-updated_at')
        
        channels_data = []
        for channel in channels:
            # Get last message
            last_message = None
            last_message_obj = Message.objects.filter(channel=channel).select_related('sender').order_by('-timestamp').first()
            if last_message_obj:
                last_message = {
                    'id': last_message_obj.id,
                    'content': last_message_obj.content,
                    'timestamp': last_message_obj.timestamp.isoformat(),
                    'sender': {
                        'id': last_message_obj.sender.id,
                        'username': last_message_obj.sender.username,
                        'first_name': last_message_obj.sender.first_name,
                        'last_name': last_message_obj.sender.last_name,
                    }
                }
            
            # Get participants info
            participants = []
            for participant in channel.participants.all():
                participants.append({
                    'id': participant.id,
                    'username': participant.username,
                    'first_name': participant.first_name,
                    'last_name': participant.last_name,
                    'email': participant.email,
                })
            
            # Get online users
            online = []
            for user in channel.online.all():
                online.append({
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                })
            
            channels_data.append({
                'id': channel.id,
                'name': channel.name,
                'is_direct': channel.is_direct,
                'created_at': channel.created_at.isoformat(),
                'updated_at': channel.updated_at.isoformat(),
                'participants': participants,
                'online': online,
                'last_message': last_message,
            })
        
        return JsonResponse({'channels': channels_data})
    
    def post(self, request):
        """Create a new channel (DM or group chat)."""
        try:
            data = json.loads(request.body)
            is_direct = data.get('is_direct', False)
            participant_ids = data.get('participant_ids', [])
            
            if not participant_ids:
                return JsonResponse({'error': 'No participants specified'}, status=400)
            
            # Verify all participants are from same schools as current user
            user_schools = get_user_schools(request.user)
            school_users_data = get_school_users(user_schools)
            valid_user_ids = {user_data['id'] for user_data in school_users_data}
            
            # Add current user to valid IDs
            valid_user_ids.add(request.user.id)
            
            # Check if all participant IDs are valid
            for pid in participant_ids:
                if pid not in valid_user_ids:
                    return JsonResponse({'error': 'Invalid participant - not in same school'}, status=400)
            
            if is_direct:
                # For DMs, ensure only 2 participants total (current user + 1 other)
                if len(participant_ids) != 1:
                    return JsonResponse({'error': 'Direct messages must have exactly 2 participants'}, status=400)
                
                other_user_id = participant_ids[0]
                
                # Check if DM already exists
                existing_dm = Channel.objects.filter(
                    is_direct=True,
                    participants=request.user
                ).filter(
                    participants=other_user_id
                ).first()
                
                if existing_dm:
                    # Return existing DM
                    participants = []
                    for participant in existing_dm.participants.all():
                        participants.append({
                            'id': participant.id,
                            'username': participant.username,
                            'first_name': participant.first_name,
                            'last_name': participant.last_name,
                            'email': participant.email,
                        })
                    
                    return JsonResponse({
                        'id': existing_dm.id,
                        'name': existing_dm.name,
                        'is_direct': existing_dm.is_direct,
                        'created_at': existing_dm.created_at.isoformat(),
                        'updated_at': existing_dm.updated_at.isoformat(),
                        'participants': participants,
                        'online': [],
                        'last_message': None,
                    })
                
                # Create new DM
                channel_name = f'DM_{min(request.user.id, other_user_id)}_{max(request.user.id, other_user_id)}'
                channel = Channel.objects.create(
                    name=channel_name,
                    is_direct=True
                )
                channel.participants.add(request.user.id, other_user_id)
            else:
                # Group chat
                channel_name = data.get('name', f'Group Chat {len(participant_ids) + 1}')
                channel = Channel.objects.create(
                    name=channel_name,
                    is_direct=False
                )
                # Add all participants including current user
                all_participant_ids = participant_ids + [request.user.id]
                channel.participants.add(*all_participant_ids)
            
            # Return channel data
            participants = []
            for participant in channel.participants.all():
                participants.append({
                    'id': participant.id,
                    'username': participant.username,
                    'first_name': participant.first_name,
                    'last_name': participant.last_name,
                    'email': participant.email,
                })
            
            return JsonResponse({
                'id': channel.id,
                'name': channel.name,
                'is_direct': channel.is_direct,
                'created_at': channel.created_at.isoformat(),
                'updated_at': channel.updated_at.isoformat(),
                'participants': participants,
                'online': [],
                'last_message': None,
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(login_required, name='dispatch')
class ChatMessagesView(View):
    """Get messages for a specific channel."""
    
    def get(self, request, channel_id):
        # Verify user is participant in this channel
        channel = get_object_or_404(
            Channel.objects.filter(participants=request.user),
            id=channel_id
        )
        
        # Get messages with pagination
        page_size = 50
        page = int(request.GET.get('page', 1))
        offset = (page - 1) * page_size
        
        messages = Message.objects.filter(
            channel=channel
        ).select_related('sender').order_by('-timestamp')[offset:offset + page_size]
        
        messages_data = []
        for message in reversed(messages):  # Reverse to show oldest first on page
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'sender': {
                    'id': message.sender.id,
                    'username': message.sender.username,
                    'first_name': message.sender.first_name,
                    'last_name': message.sender.last_name,
                },
                'file': message.file.url if message.file else None,
            })
        
        return JsonResponse({
            'messages': messages_data,
            'channel_id': channel.id,
            'has_more': messages.count() == page_size
        })
    
    def post(self, request, channel_id):
        """Send a message to a channel."""
        try:
            # Verify user is participant in this channel
            channel = get_object_or_404(
                Channel.objects.filter(participants=request.user),
                id=channel_id
            )
            
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            
            if not content:
                return JsonResponse({'error': 'Message content cannot be empty'}, status=400)
            
            # Create message
            message = Message.objects.create(
                channel=channel,
                sender=request.user,
                content=content
            )
            
            # Update channel timestamp
            channel.save()  # This updates updated_at
            
            return JsonResponse({
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'sender': {
                    'id': message.sender.id,
                    'username': message.sender.username,
                    'first_name': message.sender.first_name,
                    'last_name': message.sender.last_name,
                },
                'file': None,
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# Simple function-based views for easier integration
@login_required
@require_http_methods(["GET"])
def chat_school_users(request):
    """Get all users from the same schools as current user."""
    user_schools = get_user_schools(request.user)
    school_users = get_school_users(user_schools, exclude_user=request.user)
    
    return JsonResponse({
        'users': school_users,
        'schools': [{'id': school.id, 'name': school.name} for school in user_schools]
    })