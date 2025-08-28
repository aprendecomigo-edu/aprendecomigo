"""
Default email templates for student balance monitoring notifications - Issue #107

This module provides default templates for low balance and package expiring notifications.
These templates can be customized per school using the existing email template system.
"""

from messaging.models import EmailTemplateType

DEFAULT_LOW_BALANCE_TEMPLATE = {
    "name": "Low Balance Alert",
    "template_type": EmailTemplateType.LOW_BALANCE_ALERT,
    "subject": "Saldo Baixo - {{student_name}} | {{school_name}}",
    "html_content": """
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
            <h1 style="color: #dc3545; margin: 0;">⚠️ Saldo Baixo</h1>
        </div>

        <div style="padding: 30px 20px;">
            <p>Olá <strong>{{student_name}}</strong>,</p>

            <p>O seu saldo de horas está a ficar baixo. Tem apenas <strong>{{remaining_hours}} horas</strong> restantes na sua conta.</p>

            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
                <p style="margin: 0; color: #856404;">
                    <strong>💡 Para continuar as suas aulas:</strong><br>
                    Por favor, recarregue o seu saldo para não interromper o seu aprendizado.
                </p>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="#" style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Recarregar Saldo
                </a>
            </div>

            <p>Se tiver dúvidas, não hesite em contactar-nos.</p>

            <p>Cumprimentos,<br>
            <strong>{{school_name}}</strong></p>
        </div>

        <div style="background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #6c757d;">
            <p>Este é um email automático. Para suporte, contacte: {{support_email}}</p>
        </div>
    </div>
    """,
    "text_content": """
Olá {{student_name}},

O seu saldo de horas está a ficar baixo. Tem apenas {{remaining_hours}} horas restantes na sua conta.

Para continuar as suas aulas, por favor recarregue o seu saldo para não interromper o seu aprendizado.

Se tiver dúvidas, não hesite em contactar-nos.

Cumprimentos,
{{school_name}}

---
Este é um email automático. Para suporte, contacte: {{support_email}}
    """,
    "is_default": True,
    "description": "Template para alertas de saldo baixo enviados automaticamente aos estudantes.",
}


DEFAULT_PACKAGE_EXPIRING_TEMPLATE = {
    "name": "Package Expiring Alert",
    "template_type": EmailTemplateType.PACKAGE_EXPIRING_ALERT,
    "subject": "Pacote a Expirar - {{student_name}} | {{school_name}}",
    "html_content": """
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
            <h1 style="color: #fd7e14; margin: 0;">⏰ Pacote a Expirar</h1>
        </div>

        <div style="padding: 30px 20px;">
            <p>Olá <strong>{{student_name}}</strong>,</p>

            <p>O seu pacote de aprendizagem vai expirar em <strong>{{days_until_expiry}} dias</strong> ({{expiry_date}}).</p>

            <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 5px; padding: 15px; margin: 20px 0;">
                <p style="margin: 0; color: #0c5460;">
                    <strong>📦 Detalhes do Pacote:</strong><br>
                    Valor: €{{package_amount}}<br>
                    Expira: {{expiry_date}}
                </p>
            </div>

            <p>Para continuar a ter acesso às suas aulas, renove o seu pacote antes da data de expiração.</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="#" style="background-color: #28a745; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Renovar Pacote
                </a>
            </div>

            <p>Se tiver dúvidas, não hesite em contactar-nos.</p>

            <p>Cumprimentos,<br>
            <strong>{{school_name}}</strong></p>
        </div>

        <div style="background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #6c757d;">
            <p>Este é um email automático. Para suporte, contacte: {{support_email}}</p>
        </div>
    </div>
    """,
    "text_content": """
Olá {{student_name}},

O seu pacote de aprendizagem vai expirar em {{days_until_expiry}} dias ({{expiry_date}}).

Detalhes do Pacote:
- Valor: €{{package_amount}}
- Expira: {{expiry_date}}

Para continuar a ter acesso às suas aulas, renove o seu pacote antes da data de expiração.

Se tiver dúvidas, não hesite em contactar-nos.

Cumprimentos,
{{school_name}}

---
Este é um email automático. Para suporte, contacte: {{support_email}}
    """,
    "is_default": True,
    "description": "Template para alertas de pacotes prestes a expirar enviados automaticamente aos estudantes.",
}


def get_default_templates():
    """
    Get all default notification templates.

    Returns:
        List of default template dictionaries
    """
    return [DEFAULT_LOW_BALANCE_TEMPLATE, DEFAULT_PACKAGE_EXPIRING_TEMPLATE]
