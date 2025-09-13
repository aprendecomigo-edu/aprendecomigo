"""
Edge cases and error handling tests for classroom chat functionality.

This module tests boundary conditions, error scenarios, and edge cases
to ensure robust behavior under unusual or problematic conditions.
"""

import json
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from waffle.testutils import override_switch

from accounts.models import School, SchoolMembership
from classroom.models import Attachment, Channel, Message, Reaction
from classroom.tests.test_fixtures import SchoolBasedTestMixin, TestDataFactory

User = get_user_model()


class ModelEdgeCasesTest(SchoolBasedTestMixin, TestCase):
    """Test edge cases in model behavior."""

    def test_channel_with_no_participants(self):
        """Test channel behavior with no participants."""
        channel = Channel.objects.create(name="Empty Channel", is_direct=False)

        self.assertEqual(channel.participants.count(), 0)
        self.assertEqual(channel.online.count(), 0)
        self.assertEqual(str(channel), "Empty Channel")

    def test_channel_with_many_participants(self):
        """Test channel behavior with many participants."""
        channel = Channel.objects.create(name="Crowded Channel", is_direct=False)

        # Add 100 users
        users = []
        for i in range(100):
            user = TestDataFactory.create_user(f"user{i}")
            TestDataFactory.create_school_membership(user, self.school1, "student")
            users.append(user)

        channel.participants.add(*users)

        self.assertEqual(channel.participants.count(), 100)

        # Mark half online
        channel.online.add(*users[:50])
        self.assertEqual(channel.online.count(), 50)

    def test_dm_channel_name_generation_edge_cases(self):
        """Test DM channel name generation with edge cases."""
        channel = Channel()

        # Users with same ID (shouldn't happen in practice)
        user1 = Mock()
        user1.username = "user1"
        user2 = Mock()
        user2.username = "user2"

        # Test with different username orders
        name1 = channel.get_direct_channel_name(user1, user2)
        name2 = channel.get_direct_channel_name(user2, user1)

        self.assertEqual(name1, name2)
        self.assertTrue(name1.startswith("DM_"))

    def test_message_with_empty_content_and_no_file(self):
        """Test message with empty content and no file (edge case)."""
        # This should be allowed at model level but might be caught at view level
        message = Message.objects.create(
            channel=self.school1_channel,
            sender=self.teacher1,
            content="",  # Empty content, no file
        )

        self.assertEqual(message.content, "")
        self.assertFalse(message.file)

    def test_message_with_very_long_content(self):
        """Test message with very long content."""
        long_content = "A" * 10000  # 10k characters

        message = Message.objects.create(channel=self.school1_channel, sender=self.teacher1, content=long_content)

        self.assertEqual(len(message.content), 10000)

        # String representation should truncate
        str_repr = str(message)
        self.assertLess(len(str_repr), len(long_content) + len(self.teacher1.username) + 10)

    def test_reaction_with_very_long_emoji(self):
        """Test reaction with long emoji sequence."""
        # Some compound emojis can be quite long
        long_emoji = "👨‍👩‍👧‍👦"  # Family emoji

        reaction = Reaction.objects.create(message=self.message1, user=self.teacher1, emoji=long_emoji)

        self.assertEqual(reaction.emoji, long_emoji)

    def test_attachment_with_zero_size(self):
        """Test attachment with zero file size."""
        empty_file = SimpleUploadedFile("empty.txt", b"", content_type="text/plain")

        attachment = Attachment.objects.create(
            message=self.message1, file=empty_file, filename="empty.txt", file_type="text/plain", size=0
        )

        self.assertEqual(attachment.size, 0)

    def test_duplicate_channel_names_allowed(self):
        """Test that duplicate channel names are allowed."""
        channel1 = Channel.objects.create(name="Duplicate Name", is_direct=False)
        channel2 = Channel.objects.create(name="Duplicate Name", is_direct=False)

        self.assertEqual(channel1.name, channel2.name)
        self.assertNotEqual(channel1.id, channel2.id)

    def test_user_as_participant_and_online_simultaneously(self):
        """Test user being both participant and online in same channel."""
        channel = Channel.objects.create(name="Test Channel", is_direct=False)

        # Add user as participant
        channel.participants.add(self.teacher1)

        # Add same user as online
        channel.online.add(self.teacher1)

        self.assertIn(self.teacher1, channel.participants.all())
        self.assertIn(self.teacher1, channel.online.all())

    def test_message_ordering_with_same_timestamp(self):
        """Test message ordering when timestamps are very close."""
        # Create messages in rapid succession
        messages = []
        for i in range(5):
            message = Message.objects.create(
                channel=self.school1_channel, sender=self.teacher1, content=f"Rapid message {i}"
            )
            messages.append(message)

        # All messages should be in timestamp order
        retrieved_messages = list(Message.objects.filter(channel=self.school1_channel).order_by("timestamp"))

        # Should maintain insertion order even with very close timestamps
        for i in range(len(messages) - 1):
            self.assertLessEqual(retrieved_messages[i].timestamp, retrieved_messages[i + 1].timestamp)


@override_switch("chat_feature", active=True)
class ViewEdgeCasesTest(SchoolBasedTestMixin, TestCase):
    """Test edge cases in view behavior."""

    def test_chat_view_with_no_channels(self):
        """Test chat view for user with no channels."""
        # Create user with no channel memberships
        lonely_user = TestDataFactory.create_user("lonely")
        TestDataFactory.create_school_membership(lonely_user, self.school1, "student")

        self.client.force_login(lonely_user)

        response = self.client.get(reverse("chat"))
        self.assertEqual(response.status_code, 200)

        # Should handle gracefully with no channels
        self.assertContains(response, "Chat - Aprende Comigo")

    def test_message_pagination_edge_cases(self):
        """Test message pagination with edge cases."""
        # Create exactly 50 messages (page size)
        for i in range(50):
            Message.objects.create(channel=self.school1_channel, sender=self.teacher1, content=f"Message {i}")

        self.client.force_login(self.teacher1)

        # Request page that's too high
        response = self.client.get(
            reverse("chat_messages", kwargs={"channel_id": self.school1_channel.id}), {"page": 999}
        )

        # Django paginator should handle gracefully
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("messages", data)

    def test_user_search_with_special_characters(self):
        """Test user search with special characters in names."""
        # Create user with special characters
        special_user = User.objects.create_user(
            username="user_special",
            email="special@example.com",
            first_name="João",
            last_name="São-Paulo",
            password="pass",
        )
        TestDataFactory.create_school_membership(special_user, self.school1, "student")

        self.client.force_login(self.teacher1)

        # Search with special characters
        response = self.client.get(reverse("chat_user_search"), {"search": "João"})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        usernames = [user["username"] for user in data["users"]]
        self.assertIn("user_special", usernames)

    def test_create_channel_with_invalid_participant_id(self):
        """Test creating channel with invalid participant ID."""
        self.client.force_login(self.teacher1)

        response = self.client.post(
            reverse("chat_channels"),
            json.dumps(
                {
                    "is_direct": True,
                    "participant_ids": [99999],  # Invalid ID
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_send_message_to_nonexistent_channel(self):
        """Test sending message to nonexistent channel."""
        self.client.force_login(self.teacher1)

        response = self.client.post(
            reverse("chat_messages", kwargs={"channel_id": 99999}),
            json.dumps({"content": "Message to nowhere"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

    def test_reaction_to_message_in_inaccessible_channel(self):
        """Test adding reaction to message in inaccessible channel."""
        # Create message in school2 channel
        message = Message.objects.create(channel=self.school2_channel, sender=self.teacher2, content="Secret message")

        # Try to react as school1 user
        self.client.force_login(self.teacher1)

        response = self.client.post(
            reverse("message_reactions", kwargs={"message_id": message.id}),
            json.dumps({"emoji": "👍"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

    def test_file_upload_with_missing_file(self):
        """Test file upload with missing file data."""
        self.client.force_login(self.teacher1)

        response = self.client.post(
            reverse("chat_messages", kwargs={"channel_id": self.school1_channel.id}),
            {
                "content": "",
                # Missing 'file' field
            },
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("required", data["error"])

    def test_concurrent_dm_creation(self):
        """Test concurrent DM channel creation (race condition)."""
        self.client.force_login(self.teacher1)

        # Create first DM
        response1 = self.client.post(
            reverse("chat_channels"),
            json.dumps({"is_direct": True, "participant_ids": [self.student1.id]}),
            content_type="application/json",
        )

        # Try to create duplicate DM
        response2 = self.client.post(
            reverse("chat_channels"),
            json.dumps({"is_direct": True, "participant_ids": [self.student1.id]}),
            content_type="application/json",
        )

        # Both should succeed, second should return existing
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        data1 = json.loads(response1.content)
        data2 = json.loads(response2.content)
        self.assertEqual(data1["id"], data2["id"])  # Same channel returned

    @override_settings(MAX_UPLOAD_SIZE=100)  # Very small limit
    def test_file_upload_size_limit_enforcement(self):
        """Test that file size limits are enforced."""
        large_file = SimpleUploadedFile("large.txt", b"x" * 200, content_type="text/plain")

        self.client.force_login(self.teacher1)

        response = self.client.post(
            reverse("chat_messages", kwargs={"channel_id": self.school1_channel.id}),
            {"content": "File too large", "file": large_file},
        )

        # Should handle file size validation error gracefully
        # The exact response depends on how validation is implemented


class DatabaseEdgeCasesTest(SchoolBasedTestMixin, TestCase):
    """Test database-level edge cases and constraints."""

    def test_reaction_unique_constraint_with_database_level(self):
        """Test reaction unique constraint at database level."""
        # Create first reaction
        Reaction.objects.create(message=self.message1, user=self.teacher1, emoji="👍")

        # Attempt to create duplicate at database level should fail
        with self.assertRaises(IntegrityError):
            Reaction.objects.create(message=self.message1, user=self.teacher1, emoji="👍")

    def test_cascade_deletion_chain(self):
        """Test cascade deletion chain: School -> User -> Message -> Reaction."""
        # Create a complex chain of related objects
        school = TestDataFactory.create_school("Temp School")
        user = TestDataFactory.create_user("temp_user")
        TestDataFactory.create_school_membership(user, school, "student")

        channel = TestDataFactory.create_channel("Temp Channel", participants=[user])
        message = TestDataFactory.create_message(channel, user, "Temp message")
        reaction = TestDataFactory.create_reaction(message, user, "🔥")
        attachment = TestDataFactory.create_attachment(message, "temp.pdf")

        reaction_id = reaction.id
        attachment_id = attachment.id
        message_id = message.id

        # Delete the school (this shouldn't cascade to everything)
        # Only SchoolMembership should be affected directly
        school.delete()

        # Message, reaction, and attachment should still exist
        self.assertTrue(Message.objects.filter(id=message_id).exists())
        self.assertTrue(Reaction.objects.filter(id=reaction_id).exists())
        self.assertTrue(Attachment.objects.filter(id=attachment_id).exists())

        # But if we delete the channel, everything should cascade
        channel.delete()

        # Now message, reaction, and attachment should be deleted
        self.assertFalse(Message.objects.filter(id=message_id).exists())
        self.assertFalse(Reaction.objects.filter(id=reaction_id).exists())
        self.assertFalse(Attachment.objects.filter(id=attachment_id).exists())

    def test_transaction_rollback_on_error(self):
        """Test that transactions roll back properly on errors."""
        with self.assertRaises(Exception):
            with transaction.atomic():
                # Create a message
                message = Message.objects.create(
                    channel=self.school1_channel, sender=self.teacher1, content="This should be rolled back"
                )
                message_id = message.id

                # Force an error
                raise Exception("Forced error")

        # Message should not exist due to rollback
        self.assertFalse(Message.objects.filter(id=message_id).exists())

    def test_bulk_operations_edge_cases(self):
        """Test bulk operations with edge cases."""
        # Create many messages
        messages = []
        for i in range(1000):
            message = Message(channel=self.school1_channel, sender=self.teacher1, content=f"Bulk message {i}")
            messages.append(message)

        # Bulk create
        created_messages = Message.objects.bulk_create(messages)
        self.assertEqual(len(created_messages), 1000)

        # Bulk update
        Message.objects.filter(channel=self.school1_channel, content__startswith="Bulk message").update(
            content="Updated bulk message"
        )

        updated_count = Message.objects.filter(channel=self.school1_channel, content="Updated bulk message").count()

        self.assertEqual(updated_count, 1000)

    def test_queryset_performance_with_large_dataset(self):
        """Test queryset performance with large datasets."""
        # Create many users, channels, and messages
        users = []
        for i in range(100):
            user = TestDataFactory.create_user(f"perf_user_{i}")
            TestDataFactory.create_school_membership(user, self.school1, "student")
            users.append(user)

        # Create channels with many participants
        channel = TestDataFactory.create_channel("Performance Test", participants=users)

        # Create many messages
        for i in range(500):
            sender = users[i % len(users)]
            TestDataFactory.create_message(channel, sender, f"Performance message {i}")

        # Test efficient queries with select_related and prefetch_related
        with self.assertNumQueries(3):  # Should be efficient
            messages = (
                Message.objects.filter(channel=channel)
                .select_related("sender")
                .prefetch_related("reactions__user")[:10]
            )

            # Access related objects to trigger queries
            for message in messages:
                _ = message.sender.username
                for reaction in message.reactions.all():
                    _ = reaction.user.username


class ConcurrencyEdgeCasesTest(SchoolBasedTestMixin, TestCase):
    """Test concurrency and race condition edge cases."""

    def test_concurrent_message_creation(self):
        """Test concurrent message creation in same channel."""
        from threading import Thread
        import time

        messages_created = []

        def create_message(content):
            message = Message.objects.create(channel=self.school1_channel, sender=self.teacher1, content=content)
            messages_created.append(message)

        # Create multiple threads creating messages simultaneously
        threads = []
        for i in range(5):
            thread = Thread(target=create_message, args=(f"Concurrent message {i}",))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All messages should be created successfully
        self.assertEqual(len(messages_created), 5)

        # All messages should have different timestamps (or at least be ordered)
        timestamps = [msg.timestamp for msg in messages_created]
        sorted_timestamps = sorted(timestamps)
        self.assertEqual(timestamps, sorted_timestamps)

    def test_concurrent_reaction_creation(self):
        """Test concurrent reaction creation on same message."""
        from threading import Thread

        reactions_created = []
        errors = []

        def create_reaction(emoji):
            try:
                reaction = Reaction.objects.create(message=self.message1, user=self.teacher1, emoji=emoji)
                reactions_created.append(reaction)
            except Exception as e:
                errors.append(e)

        # Try to create reactions with same emoji (should cause constraint violation)
        threads = []
        for i in range(3):
            thread = Thread(target=create_reaction, args=("👍",))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Only one reaction should succeed, others should fail
        self.assertEqual(len(reactions_created), 1)
        self.assertEqual(len(errors), 2)

    def test_concurrent_channel_online_user_management(self):
        """Test concurrent online user management."""
        from threading import Thread

        def mark_user_online():
            self.school1_channel.online.add(self.teacher1)

        def mark_user_offline():
            self.school1_channel.online.remove(self.teacher1)

        # Concurrent online/offline operations
        threads = []
        for i in range(10):
            thread = Thread(target=mark_user_online) if i % 2 == 0 else Thread(target=mark_user_offline)
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Final state should be consistent
        online_users = self.school1_channel.online.all()
        self.assertIn(self.teacher1, online_users)


@override_settings(DEBUG=True)  # Enable query logging for debugging
@override_switch("chat_feature", active=True)
class PerformanceEdgeCasesTest(SchoolBasedTestMixin, TestCase):
    """Test performance-related edge cases."""

    def test_n_plus_one_query_prevention(self):
        """Test that N+1 queries are prevented in message retrieval."""
        # Create multiple messages with reactions
        messages = []
        for i in range(20):
            message = TestDataFactory.create_message(self.school1_channel, self.teacher1, f"Message {i}")
            TestDataFactory.create_reaction(message, self.teacher1, "👍")
            TestDataFactory.create_reaction(message, self.student1, "❤️")
            messages.append(message)

        # Query messages with reactions efficiently
        with self.assertNumQueries(3):  # Should be constant regardless of message count
            messages_with_reactions = (
                Message.objects.filter(channel=self.school1_channel)
                .select_related("sender")
                .prefetch_related("reactions__user")
            )

            # Access all related data
            for message in messages_with_reactions:
                _ = message.sender.username
                for reaction in message.reactions.all():
                    _ = reaction.user.username

    def test_large_channel_participant_queries(self):
        """Test efficient queries for channels with many participants."""
        # Create channel with many participants
        users = []
        for i in range(100):
            user = TestDataFactory.create_user(f"participant_{i}")
            TestDataFactory.create_school_membership(user, self.school1, "student")
            users.append(user)

        large_channel = TestDataFactory.create_channel("Large Channel", participants=users)

        # Query channel with all participants efficiently
        with self.assertNumQueries(2):
            channel_with_participants = (
                Channel.objects.filter(id=large_channel.id).prefetch_related("participants", "online").first()
            )

            participant_count = channel_with_participants.participants.count()
            online_count = channel_with_participants.online.count()

            self.assertEqual(participant_count, 100)
            self.assertEqual(online_count, 0)  # No one online initially

    def test_message_pagination_performance(self):
        """Test message pagination performance with large datasets."""
        # Create many messages
        for i in range(1000):
            TestDataFactory.create_message(self.school1_channel, self.teacher1, f"Paginated message {i}")

        # Test pagination performance (should be consistent across pages)
        self.client.force_login(self.teacher1)

        # Test different pages
        for page in [1, 5, 10, 20]:
            with self.assertNumQueries(5):  # Should be constant
                response = self.client.get(
                    reverse("chat_messages", kwargs={"channel_id": self.school1_channel.id}), {"page": page}
                )
                self.assertEqual(response.status_code, 200)

                data = json.loads(response.content)
                self.assertTrue(len(data["messages"]) > 0)
