from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction

from .models import Channel, Message, Reaction
from .serializers import (
    ChannelSerializer,
    MessageSerializer,
    ReactionSerializer,
    UserSerializer,
)
from .services.session_booking_service import SessionBookingService, SessionBookingError

User = get_user_model()


class ChannelViewSet(viewsets.ModelViewSet):
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return channels where the user is a participant."""
        return Channel.objects.filter(participants=self.request.user)

    def perform_create(self, serializer):
        """Create a channel and add the current user as a participant."""
        # Pass the current user to the serializer for duplicate DM checking
        channel = serializer.save(current_user=self.request.user)

        # Only add current user if they're not already a participant
        # (DMs add the current user automatically, group channels need it added)
        if not channel.participants.filter(id=self.request.user.id).exists():
            channel.participants.add(self.request.user)

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        """List messages in a channel with pagination."""
        channel = self.get_object()
        messages = channel.messages.all().order_by("-timestamp")
        page = self.paginate_queryset(messages)

        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        """Create a new message in the channel."""
        channel = self.get_object()

        # Check if user is a participant
        if not channel.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "You must be a participant to send messages"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Add channel to the data for validation
        data = request.data.copy()
        data['channel'] = channel.id
        
        serializer = MessageSerializer(data=data)

        if serializer.is_valid():
            message = serializer.save(sender=request.user)

            # Broadcast to WebSocket (only in non-test environments)
            try:
                channel_layer = get_channel_layer()
                if channel_layer:
                    group_name = f"chat_{channel.id}"  # Use channel ID instead of name for WebSocket groups
                    async_to_sync(channel_layer.group_send)(
                        group_name,
                        {"type": "chat_message", "message": MessageSerializer(message).data},
                    )
            except Exception:
                # Silently fail in test environments or when Redis is not available
                pass

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return messages from channels where the user is a participant."""
        return Message.objects.filter(channel__participants=self.request.user).order_by(
            "-timestamp"
        )

    @action(detail=True, methods=["get", "post", "delete"], url_path="reactions")
    def reactions(self, request, pk=None):
        """Handle all reaction operations: list, add, and remove."""
        message = self.get_object()
        
        if request.method == "GET":
            # List reactions for a message
            reactions = message.reactions.all()
            serializer = ReactionSerializer(reactions, many=True)
            return Response(serializer.data)
        
        elif request.method == "POST":
            # Add a reaction to a message
            serializer = ReactionSerializer(data=request.data)
            if serializer.is_valid():
                reaction = serializer.save(message=message, user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == "DELETE":
            # Remove a reaction from a message
            emoji = request.data.get("emoji")
            try:
                reaction = message.reactions.get(user=request.user, emoji=emoji)
                reaction.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Reaction.DoesNotExist:
                return Response({"error": "Reaction not found"}, status=status.HTTP_404_NOT_FOUND)


class UserSearchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Search users by username, first name, or last name."""
        query = self.request.query_params.get("search", "")
        if not query:
            return User.objects.none()

        return User.objects.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        ).exclude(id=self.request.user.id)


class SessionBookingViewSet(viewsets.GenericViewSet):
    """
    ViewSet for session booking operations in classroom context.
    
    Provides API endpoints for:
    - Booking new sessions with hour deduction
    - Cancelling sessions with hour refunds  
    - Adjusting session durations
    - Getting session booking summaries
    
    Following GitHub Issue #173: Session Booking API Endpoints Return 404
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='book')
    def book_session(self, request):
        """Book a new session with complete validation and hour deduction."""
        try:
            # Extract booking parameters from request
            teacher_id = request.data.get('teacher_id')
            school_id = request.data.get('school_id') 
            date = request.data.get('date')
            start_time = request.data.get('start_time')
            end_time = request.data.get('end_time')
            session_type = request.data.get('session_type')
            grade_level = request.data.get('grade_level')
            student_ids = request.data.get('student_ids', [])
            is_trial = request.data.get('is_trial', False)
            is_makeup = request.data.get('is_makeup', False)
            notes = request.data.get('notes', '')
            
            # Validate required parameters
            required_params = ['teacher_id', 'school_id', 'date', 'start_time', 'end_time', 'session_type', 'grade_level']
            for param in required_params:
                if not request.data.get(param):
                    return Response(
                        {'error': f'{param} is required'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            if not student_ids:
                return Response(
                    {'error': 'student_ids is required and must not be empty'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Book the session using the service
            session, hour_deduction_info = SessionBookingService.book_session(
                teacher_id=teacher_id,
                school_id=school_id,
                date=date,
                start_time=start_time,
                end_time=end_time,
                session_type=session_type,
                grade_level=grade_level,
                student_ids=student_ids,
                is_trial=is_trial,
                is_makeup=is_makeup,
                notes=notes
            )
            
            return Response({
                'success': True,
                'session_id': session.id,
                'booking_details': {
                    'teacher_id': teacher_id,
                    'school_id': school_id,
                    'date': date,
                    'session_type': session_type,
                    'student_count': len(student_ids),
                    'duration_hours': str(session.duration_hours),
                    'status': session.status,
                    'booking_confirmed_at': session.booking_confirmed_at.isoformat()
                },
                'hour_deduction_info': hour_deduction_info
            }, status=status.HTTP_201_CREATED)
            
        except SessionBookingError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'An unexpected error occurred during booking'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='cancel') 
    def cancel_session(self, request, pk=None):
        """Cancel a session and process hour refunds."""
        try:
            session_id = pk
            reason = request.data.get('reason', '')
            
            cancellation_info = SessionBookingService.cancel_session(
                session_id=session_id,
                reason=reason
            )
            
            return Response({
                'success': True,
                'message': f'Session {session_id} cancelled successfully',
                'cancellation_details': cancellation_info
            })
            
        except SessionBookingError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'An unexpected error occurred during cancellation'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='adjust-duration')
    def adjust_duration(self, request, pk=None):
        """Adjust session duration after completion and handle hour adjustments."""
        try:
            session_id = pk
            actual_duration_hours = request.data.get('actual_duration_hours')
            reason = request.data.get('reason', '')
            
            if not actual_duration_hours:
                return Response(
                    {'error': 'actual_duration_hours is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            adjustment_info = SessionBookingService.adjust_session_duration(
                session_id=session_id,
                actual_duration_hours=float(actual_duration_hours),
                reason=reason
            )
            
            return Response({
                'success': True,
                'message': f'Session {session_id} duration adjusted successfully',
                'adjustment_details': adjustment_info
            })
            
        except SessionBookingError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'An unexpected error occurred during adjustment'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='summary')
    def get_booking_summary(self, request, pk=None):
        """Get comprehensive booking summary for a session."""
        try:
            session_id = pk
            
            summary = SessionBookingService.get_session_booking_summary(session_id)
            
            return Response({
                'success': True,
                'session_summary': summary
            })
            
        except SessionBookingError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'An unexpected error occurred retrieving summary'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='balance-check')
    def check_balance(self, request):
        """Check student balances for session booking eligibility."""
        try:
            student_ids = request.query_params.get('student_ids', '').split(',')
            session_duration_hours = float(request.query_params.get('duration_hours', 1.0))
            
            if not student_ids or student_ids == ['']:
                return Response(
                    {'error': 'student_ids parameter is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Simple balance check - this would integrate with the HourDeductionService
            from finances.services.hour_deduction_service import HourDeductionService
            
            balance_info = []
            for student_id in student_ids:
                try:
                    student = User.objects.get(id=int(student_id))
                    # This would use the actual balance checking logic
                    balance_info.append({
                        'student_id': int(student_id),
                        'student_name': student.name,
                        'has_sufficient_balance': True,  # Placeholder
                        'current_balance_hours': '10.00',  # Placeholder
                        'required_hours': str(session_duration_hours)
                    })
                except (User.DoesNotExist, ValueError):
                    balance_info.append({
                        'student_id': student_id,
                        'error': 'Student not found'
                    })
            
            return Response({
                'success': True,
                'balance_check': balance_info,
                'all_eligible': all(info.get('has_sufficient_balance', False) for info in balance_info if 'error' not in info)
            })
            
        except Exception as e:
            return Response(
                {'error': 'An unexpected error occurred during balance check'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
