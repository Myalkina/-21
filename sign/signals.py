from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


@receiver(post_save, sender=User)
def send_welcome_email_on_signup(sender, instance, created, **kwargs):
    """
    Отправляем письмо с подтверждением при регистрации
    """
    if created and instance.email:
        # Генерируем токен для подтверждения
        token = default_token_generator.make_token(instance)
        uid = urlsafe_base64_encode(force_bytes(instance.pk))

        confirmation_link = f"{settings.SITE_URL}{reverse('account_confirm_email', kwargs={'key': token})}"

        # HTML версия письма
        context = {
            'user': instance,
            'confirmation_link': confirmation_link,
            'site_url': settings.SITE_URL,
        }

        subject = 'Добро пожаловать! Подтвердите ваш email'
        html_content = render_to_string('account/email/welcome_confirmation_email.html', context)
        text_content = f"Добро пожаловать, {instance.username}! Подтвердите ваш email: {confirmation_link}"

        # Отправка письма
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [instance.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()


@receiver(post_save, sender=EmailAddress)
def send_welcome_email_after_confirmation(sender, instance, created, **kwargs):
    """
    Отправляем приветственное письмо после подтверждения email
    """
    if instance.verified and not created and instance.primary:
        context = {
            'user': instance.user,
            'login_url': f"{settings.SITE_URL}{reverse('account_login')}",
            'site_url': settings.SITE_URL,
        }

        subject = 'Добро пожаловать на наш сайт!'
        html_content = render_to_string('account/email/welcome_complete_email.html', context)
        text_content = f"Приветствуем, {instance.user.username}! Ваш аккаунт активирован."

        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [instance.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()