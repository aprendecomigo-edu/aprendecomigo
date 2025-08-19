"""
Default Email Templates for Teacher Communications (Issue #99)

This module provides default professional email templates for all communication types.
Templates are designed to be responsive, accessible, and consistent across email clients.
"""

from ..models import EmailTemplateType


class DefaultEmailTemplates:
    """
    Provider of default email templates for different communication types.
    """

    # Base HTML template structure for consistent styling
    BASE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        .email-container {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .header {
            text-align: center;
            border-bottom: 3px solid {{ school_primary_color }};
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .logo {
            font-size: 28px;
            font-weight: bold;
            color: {{ school_primary_color }};
            margin-bottom: 10px;
        }
        .school-info {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid {{ school_primary_color }};
        }
        .school-name {
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }
        .cta-section {
            text-align: center;
            margin: 30px 0;
        }
        .cta-button {
            display: inline-block;
            background-color: {{ school_primary_color }};
            color: white;
            text-decoration: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            margin: 10px 0;
            transition: background-color 0.3s;
        }
        .cta-button:hover {
            background-color: {{ school_secondary_color }};
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 14px;
            color: #6c757d;
        }
        .footer-links {
            margin: 15px 0;
        }
        .footer-links a {
            color: {{ school_primary_color }};
            text-decoration: none;
            margin: 0 10px;
        }
        .footer-links a:hover {
            text-decoration: underline;
        }
        @media (max-width: 600px) {
            body {
                padding: 10px;
            }
            .email-container {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            {% if school_logo_url %}
            <img src="{{ school_logo_url }}" alt="{{ school_name }}" style="max-height: 60px; margin-bottom: 10px;">
            {% else %}
            <div class="logo">📚 {{ school_name }}</div>
            {% endif %}
            <p>{{ platform_name }} Educational Platform</p>
        </div>

        {CONTENT}

        <div class="footer">
            <p><strong>{{ school_name }} Team</strong></p>
            {% if school_website %}
            <div class="footer-links">
                <a href="{{ school_website }}">Visit Website</a>
                <a href="{{ platform_url }}/support">Support</a>
                <a href="{{ platform_url }}/privacy">Privacy Policy</a>
            </div>
            {% endif %}
            <p>This email was sent to {{ recipient_email }} from {{ school_name }}.</p>
            <p style="font-size: 12px; color: #999;">
                If you didn't expect this email, you can safely ignore it.
            </p>
        </div>
    </div>
</body>
</html>"""

    @classmethod
    def get_default_template(cls, template_type: str) -> dict[str, str]:
        """
        Get the default template for a specific type.

        Args:
            template_type: Type of email template

        Returns:
            Dictionary with template data
        """
        template_methods = {
            EmailTemplateType.INVITATION: cls._get_invitation_template,
            EmailTemplateType.REMINDER: cls._get_reminder_template,
            EmailTemplateType.WELCOME: cls._get_welcome_template,
            EmailTemplateType.PROFILE_REMINDER: cls._get_profile_reminder_template,
            EmailTemplateType.COMPLETION_CELEBRATION: cls._get_completion_celebration_template,
            EmailTemplateType.ONGOING_SUPPORT: cls._get_ongoing_support_template,
        }

        enum_template_type = EmailTemplateType(template_type)
        if enum_template_type in template_methods:
            return template_methods[enum_template_type]()
        else:
            raise ValueError(f"Unknown template type: {template_type}")

    @classmethod
    def _get_invitation_template(cls) -> dict[str, str]:
        """Get the default teacher invitation template."""
        return {
            "name": "Default Teacher Invitation",
            "subject": "Teacher Invitation: Join {{ school_name }} on {{ platform_name }}",
            "html": cls.BASE_HTML_TEMPLATE.replace(
                "{CONTENT}",
                """
                <h1 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">You're Invited to Join as a Teacher!</h1>

                <p>Hello,</p>

                <p>We're excited to invite you to join <strong>{{ school_name }}</strong> as a teacher on the {{ platform_name }} platform. This is a wonderful opportunity to share your knowledge and help students achieve their educational goals.</p>

                <div class="school-info">
                    <div class="school-name">{{ school_name }}</div>
                    <div style="color: #6c757d; font-size: 16px; margin-bottom: 5px;">Role: {{ role_display }}</div>
                    {% if school_description %}
                    <p style="margin-top: 10px; color: #6c757d;">{{ school_description }}</p>
                    {% endif %}
                </div>

                {% if custom_message %}
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <div style="font-weight: bold; color: #856404; margin-bottom: 8px;">Personal Message from {{ invited_by_name }}:</div>
                    <p>{{ custom_message }}</p>
                </div>
                {% endif %}

                <div class="cta-section">
                    <a href="{{ invitation_link }}" class="cta-button">Accept Invitation</a>
                    <p style="margin-top: 15px; font-size: 14px; color: #6c757d;">
                        Click the button above to accept your invitation and get started
                    </p>
                </div>

                <div style="background-color: #fff5f5; border: 1px solid #feb2b2; color: #c53030; padding: 12px; border-radius: 6px; margin: 15px 0; font-size: 14px;">
                    <strong>⏰ Time Sensitive:</strong> This invitation expires on {{ expires_at|date:"F j, Y" }}. Please accept it soon to avoid missing this opportunity.
                </div>

                <p><strong>What happens next?</strong></p>
                <ol>
                    <li>Click the "Accept Invitation" button above</li>
                    <li>Complete your teacher profile setup</li>
                    <li>Start teaching and helping students learn</li>
                </ol>

                <p>If you're unable to click the button, you can copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace;">{{ invitation_link }}</p>

                <p>If you have any questions about this invitation or the platform, please don't hesitate to contact {{ invited_by_name }} at {{ invited_by_email }}.</p>

                <p>Welcome to the {{ platform_name }} community!</p>
            """,
            ),
            "text": """You're Invited to Join {{ school_name }} as a Teacher!

Hello,

We're excited to invite you to join {{ school_name }} as a teacher on the {{ platform_name }} platform. This is a wonderful opportunity to share your knowledge and help students achieve their educational goals.

School: {{ school_name }}
Role: {{ role_display }}
{% if school_description %}
About the school: {{ school_description }}
{% endif %}

{% if custom_message %}
Personal Message from {{ invited_by_name }}:
{{ custom_message }}
{% endif %}

To accept this invitation, please visit:
{{ invitation_link }}

⏰ IMPORTANT: This invitation expires on {{ expires_at|date:"F j, Y" }}.

What happens next?
1. Click the invitation link above
2. Complete your teacher profile setup
3. Start teaching and helping students learn

If you have any questions, please contact {{ invited_by_name }} at {{ invited_by_email }}.

Welcome to the {{ platform_name }} community!

Best regards,
The {{ school_name }} Team

---
This email was sent to {{ recipient_email }} from {{ school_name }}.
If you didn't expect this invitation, you can safely ignore this email.
""",
        }

    @classmethod
    def _get_reminder_template(cls) -> dict[str, str]:
        """Get the default reminder template."""
        return {
            "name": "Default Invitation Reminder",
            "subject": "Reminder: Your invitation to join {{ school_name }} expires soon",
            "html": cls.BASE_HTML_TEMPLATE.replace(
                "{CONTENT}",
                """
                <h1 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">Reminder: Your Teacher Invitation</h1>

                <p>Hello,</p>

                <p>We wanted to remind you about your pending invitation to join <strong>{{ school_name }}</strong> as a teacher on {{ platform_name }}.</p>

                <div class="school-info">
                    <div class="school-name">{{ school_name }}</div>
                    <div style="color: #6c757d; font-size: 16px;">Role: {{ role_display }}</div>
                </div>

                <div style="background-color: #fff5f5; border: 1px solid #feb2b2; color: #c53030; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <strong>⏰ Time Sensitive:</strong> Your invitation expires on {{ expires_at|date:"F j, Y \a\\t g:i A" }}. Don't miss this opportunity!
                </div>

                <div class="cta-section">
                    <a href="{{ invitation_link }}" class="cta-button">Accept Invitation Now</a>
                </div>

                <p>Joining {{ school_name }} means:</p>
                <ul>
                    <li>✅ Flexible teaching schedule</li>
                    <li>✅ Professional development opportunities</li>
                    <li>✅ Supportive teaching community</li>
                    <li>✅ Modern teaching tools and resources</li>
                </ul>

                <p>If you have any questions or concerns, please reach out to {{ invited_by_name }} at {{ invited_by_email }}.</p>

                <p>We hope to welcome you to our team soon!</p>
            """,
            ),
            "text": """Reminder: Your Teacher Invitation Expires Soon

Hello,

We wanted to remind you about your pending invitation to join {{ school_name }} as a teacher on {{ platform_name }}.

School: {{ school_name }}
Role: {{ role_display }}

⏰ IMPORTANT: Your invitation expires on {{ expires_at|date:"F j, Y \a\\t g:i A" }}.

To accept your invitation, visit:
{{ invitation_link }}

Joining {{ school_name }} means:
✅ Flexible teaching schedule
✅ Professional development opportunities
✅ Supportive teaching community
✅ Modern teaching tools and resources

If you have any questions, please contact {{ invited_by_name }} at {{ invited_by_email }}.

We hope to welcome you to our team soon!

Best regards,
The {{ school_name }} Team
""",
        }

    @classmethod
    def _get_welcome_template(cls) -> dict[str, str]:
        """Get the default welcome template."""
        return {
            "name": "Default Welcome Message",
            "subject": "Welcome to {{ school_name }}! Your journey begins now",
            "html": cls.BASE_HTML_TEMPLATE.replace(
                "{CONTENT}",
                """
                <h1 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">🎉 Welcome to {{ school_name }}!</h1>

                <p>Dear {{ teacher_name }},</p>

                <p>Congratulations! You have successfully joined <strong>{{ school_name }}</strong> as a teacher. We're thrilled to have you as part of our educational community.</p>

                <div style="background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <strong>🎯 Your Next Steps:</strong>
                    <ol style="margin-top: 10px; margin-bottom: 0;">
                        <li>Complete your teacher profile</li>
                        <li>Explore the teaching dashboard</li>
                        <li>Set up your availability</li>
                        <li>Review student matching preferences</li>
                    </ol>
                </div>

                <div class="cta-section">
                    <a href="{{ dashboard_link }}" class="cta-button">Go to Dashboard</a>
                </div>

                <p><strong>What's available to you:</strong></p>
                <ul>
                    <li>📊 Comprehensive teaching dashboard</li>
                    <li>👥 Student management tools</li>
                    <li>📅 Flexible scheduling system</li>
                    <li>💬 Communication platform</li>
                    <li>📈 Progress tracking tools</li>
                    <li>🎓 Professional development resources</li>
                </ul>

                <p>If you need any help getting started, our support team is here for you. You can also reach out to {{ invited_by_name }} at {{ invited_by_email }}.</p>

                <p>We're excited to see the positive impact you'll make on our students' learning journey!</p>

                <p>Best regards,<br>The {{ school_name }} Team</p>
            """,
            ),
            "text": """🎉 Welcome to {{ school_name }}!

Dear {{ teacher_name }},

Congratulations! You have successfully joined {{ school_name }} as a teacher. We're thrilled to have you as part of our educational community.

🎯 Your Next Steps:
1. Complete your teacher profile
2. Explore the teaching dashboard
3. Set up your availability
4. Review student matching preferences

Access your dashboard: {{ dashboard_link }}

What's available to you:
📊 Comprehensive teaching dashboard
👥 Student management tools
📅 Flexible scheduling system
💬 Communication platform
📈 Progress tracking tools
🎓 Professional development resources

If you need any help getting started, our support team is here for you. You can also reach out to {{ invited_by_name }} at {{ invited_by_email }}.

We're excited to see the positive impact you'll make on our students' learning journey!

Best regards,
The {{ school_name }} Team
""",
        }

    @classmethod
    def _get_profile_reminder_template(cls) -> dict[str, str]:
        """Get the default profile completion reminder template."""
        return {
            "name": "Default Profile Completion Reminder",
            "subject": "Complete your {{ school_name }} teacher profile to get started",
            "html": cls.BASE_HTML_TEMPLATE.replace(
                "{CONTENT}",
                """
                <h1 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">Complete Your Teacher Profile</h1>

                <p>Hello {{ teacher_name }},</p>

                <p>Welcome to {{ school_name }}! We noticed that your teacher profile is still incomplete. Completing your profile is essential to start teaching and connecting with students.</p>

                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <strong>📝 Profile Completion Status:</strong>
                    <div style="margin-top: 10px;">
                        <div style="background-color: #e9ecef; border-radius: 10px; height: 20px; margin: 10px 0;">
                            <div style="background-color: {{ school_primary_color }}; width: {{ profile_completion_percentage }}%; height: 20px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-size: 12px; font-weight: bold;">
                                {{ profile_completion_percentage }}%
                            </div>
                        </div>
                    </div>
                </div>

                <p><strong>Missing Information:</strong></p>
                <ul>
                    {% for missing_field in missing_profile_fields %}
                    <li>{{ missing_field }}</li>
                    {% endfor %}
                </ul>

                <div class="cta-section">
                    <a href="{{ profile_completion_link }}" class="cta-button">Complete Your Profile</a>
                    <p style="margin-top: 15px; font-size: 14px; color: #6c757d;">
                        Takes only 5-10 minutes to complete
                    </p>
                </div>

                <p><strong>Why complete your profile?</strong></p>
                <ul>
                    <li>🎯 Get matched with suitable students</li>
                    <li>💰 Start earning from teaching</li>
                    <li>📈 Build your teaching reputation</li>
                    <li>🌟 Stand out to parents and students</li>
                </ul>

                <p>If you need help completing your profile, don't hesitate to contact us at {{ support_email }} or reach out to {{ invited_by_name }}.</p>

                <p>We're here to support your teaching journey!</p>
            """,
            ),
            "text": """Complete Your {{ school_name }} Teacher Profile

Hello {{ teacher_name }},

Welcome to {{ school_name }}! We noticed that your teacher profile is still incomplete. Completing your profile is essential to start teaching and connecting with students.

📝 Profile Completion: {{ profile_completion_percentage }}%

Missing Information:
{% for missing_field in missing_profile_fields %}
- {{ missing_field }}
{% endfor %}

Complete your profile: {{ profile_completion_link }}
(Takes only 5-10 minutes)

Why complete your profile?
🎯 Get matched with suitable students
💰 Start earning from teaching
📈 Build your teaching reputation
🌟 Stand out to parents and students

If you need help, contact us at {{ support_email }} or reach out to {{ invited_by_name }}.

We're here to support your teaching journey!

Best regards,
The {{ school_name }} Team
""",
        }

    @classmethod
    def _get_completion_celebration_template(cls) -> dict[str, str]:
        """Get the default profile completion celebration template."""
        return {
            "name": "Default Profile Completion Celebration",
            "subject": "Profile Complete! You're ready to teach at {{ school_name }}",
            "html": cls.BASE_HTML_TEMPLATE.replace(
                "{CONTENT}",
                """
                <h1 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">🎉 Congratulations, {{ teacher_name }}!</h1>

                <p>Fantastic news! You've successfully completed your teacher profile at {{ school_name }}. You're now ready to start your teaching journey with us.</p>

                <div style="background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                    <h3 style="margin-top: 0; color: #155724;">🌟 Your Profile is 100% Complete! 🌟</h3>
                    <p style="margin-bottom: 0;">You can now receive student requests and start teaching.</p>
                </div>

                <div class="cta-section">
                    <a href="{{ dashboard_link }}" class="cta-button">View Your Dashboard</a>
                </div>

                <p><strong>What's next?</strong></p>
                <ol>
                    <li>🎯 <strong>Set Your Availability:</strong> Let students know when you're free to teach</li>
                    <li>📚 <strong>Choose Your Subjects:</strong> Select the subjects you want to teach</li>
                    <li>💰 <strong>Set Your Rates:</strong> Configure your hourly teaching rates</li>
                    <li>👥 <strong>Wait for Requests:</strong> Students will start reaching out soon!</li>
                </ol>

                <div style="background-color: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="color: #1976d2; margin-top: 0;">💡 Pro Tips for New Teachers:</h4>
                    <ul style="margin-bottom: 0;">
                        <li>Upload a professional profile photo to attract more students</li>
                        <li>Write a compelling bio highlighting your expertise</li>
                        <li>Respond quickly to student requests</li>
                        <li>Be flexible with your availability initially</li>
                    </ul>
                </div>

                <p>The {{ school_name }} team is excited to have you aboard. If you have any questions or need support, please don't hesitate to reach out to us.</p>

                <p>Happy teaching!</p>
            """,
            ),
            "text": """🎉 Congratulations, {{ teacher_name }}!

Fantastic news! You've successfully completed your teacher profile at {{ school_name }}. You're now ready to start your teaching journey with us.

🌟 Your Profile is 100% Complete! 🌟
You can now receive student requests and start teaching.

Access your dashboard: {{ dashboard_link }}

What's next?
1. 🎯 Set Your Availability: Let students know when you're free to teach
2. 📚 Choose Your Subjects: Select the subjects you want to teach
3. 💰 Set Your Rates: Configure your hourly teaching rates
4. 👥 Wait for Requests: Students will start reaching out soon!

💡 Pro Tips for New Teachers:
- Upload a professional profile photo to attract more students
- Write a compelling bio highlighting your expertise
- Respond quickly to student requests
- Be flexible with your availability initially

The {{ school_name }} team is excited to have you aboard. If you have any questions or need support, please don't hesitate to reach out to us.

Happy teaching!

Best regards,
The {{ school_name }} Team
""",
        }

    @classmethod
    def _get_ongoing_support_template(cls) -> dict[str, str]:
        """Get the default ongoing support template."""
        return {
            "name": "Default Ongoing Support",
            "subject": "How are you doing at {{ school_name }}? We are here to help!",
            "html": cls.BASE_HTML_TEMPLATE.replace(
                "{CONTENT}",
                """
                <h1 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">We are Here to Support You!</h1>

                <p>Hello {{ teacher_name }},</p>

                <p>We hope you're enjoying your teaching experience at {{ school_name }}! As part of our commitment to supporting our teachers, we wanted to check in and see how things are going.</p>

                {% if teaching_stats %}
                <div style="background-color: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="color: #1976d2; margin-top: 0;">📊 Your Teaching Impact So Far:</h4>
                    <ul style="margin-bottom: 0;">
                        <li>Students taught: {{ teaching_stats.students_count }}</li>
                        <li>Hours taught: {{ teaching_stats.hours_taught }}</li>
                        <li>Average rating: {{ teaching_stats.average_rating }}/5</li>
                        <li>Subjects covered: {{ teaching_stats.subjects_count }}</li>
                    </ul>
                </div>
                {% endif %}

                <p><strong>Resources available to you:</strong></p>
                <ul>
                    <li>📚 <strong>Teaching Resources:</strong> Access our library of educational materials</li>
                    <li>💬 <strong>Teacher Community:</strong> Connect with fellow educators</li>
                    <li>🎓 <strong>Professional Development:</strong> Free workshops and training sessions</li>
                    <li>🆘 <strong>24/7 Support:</strong> Our team is always here to help</li>
                </ul>

                <div class="cta-section">
                    <a href="{{ resources_link }}" class="cta-button">Explore Resources</a>
                </div>

                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <strong>💡 Need Help?</strong>
                    <p style="margin-bottom: 0;">Whether you have questions about the platform, need teaching tips, or want to share feedback, we're here for you!</p>
                </div>

                <p><strong>Quick ways to get support:</strong></p>
                <ul>
                    <li>📧 Email us at {{ support_email }}</li>
                    <li>💬 Use the in-app chat feature</li>
                    <li>📞 Schedule a call with our support team</li>
                    <li>🌐 Visit our help center at {{ help_center_link }}</li>
                </ul>

                <p>Your success as a teacher is our priority. We're committed to providing you with everything you need to excel in your teaching journey.</p>

                <p>Keep up the great work!</p>
            """,
            ),
            "text": """We're Here to Support You! 🤝

Hello {{ teacher_name }},

We hope you're enjoying your teaching experience at {{ school_name }}! As part of our commitment to supporting our teachers, we wanted to check in and see how things are going.

{% if teaching_stats %}
📊 Your Teaching Impact So Far:
- Students taught: {{ teaching_stats.students_count }}
- Hours taught: {{ teaching_stats.hours_taught }}
- Average rating: {{ teaching_stats.average_rating }}/5
- Subjects covered: {{ teaching_stats.subjects_count }}
{% endif %}

Resources available to you:
📚 Teaching Resources: Access our library of educational materials
💬 Teacher Community: Connect with fellow educators
🎓 Professional Development: Free workshops and training sessions
🆘 24/7 Support: Our team is always here to help

Explore resources: {{ resources_link }}

💡 Need Help?
Whether you have questions about the platform, need teaching tips, or want to share feedback, we're here for you!

Quick ways to get support:
📧 Email us at {{ support_email }}
💬 Use the in-app chat feature
📞 Schedule a call with our support team
🌐 Visit our help center at {{ help_center_link }}

Your success as a teacher is our priority. We're committed to providing you with everything you need to excel in your teaching journey.

Keep up the great work!

Best regards,
The {{ school_name }} Team
""",
        }

    @classmethod
    def get_all_default_templates(cls) -> dict[str, dict[str, str]]:
        """
        Get all default templates for easy access.

        Returns:
            Dictionary mapping template types to template data
        """
        templates = {}
        for template_type in EmailTemplateType.values:
            templates[template_type] = cls.get_default_template(template_type)
        return templates
