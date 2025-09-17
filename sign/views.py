from django.contrib.auth.models import User
from django.views.generic.edit import CreateView
from .models import BaseRegisterForm
from django.shortcuts import redirect, render
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_decode
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives  # Импортируем класс для создания объекта письма с html
from django.template.loader import render_to_string  # Импортируем функцию, которая срендерит наш html в текст

from allauth.account.views import SignupView

class BaseRegisterView(CreateView):
    model = User
    form_class = BaseRegisterForm
    success_url = '/'

@login_required
def upgrade_me(request):
    user = request.user
    authors_group = Group.objects.get(name='authors')
    if not request.user.groups.filter(name='authors').exists():
        authors_group.user_set.add(user)
    return redirect('/')

def send_confirmation_email(user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    confirmation_link = f"http://yourdomain.com{reverse('confirm_email', kwargs={'uidb64': uid, 'token': token})}"

    subject = 'Подтверждение электронной почты'
    message = f'Пожалуйста, подтвердите вашу электронную почту, перейдя по следующей ссылке: {confirmation_link}'

    # Отправка письма
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


def confirm_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
        if default_token_generator.check_token(user, token):
            user.is_active = True  # Активируем пользователя
            user.save()
            messages.success(request, 'Ваша электронная почта успешно подтверждена!')
            return redirect('email_confirmed')  # Переход на страницу подтверждения
        else:
            messages.error(request, 'Ссылка для подтверждения недействительна.')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Ошибка подтверждения электронной почты.')

    return render(request, 'sign/confirm_email.html', {'user': user})


# Пример использования EmailMultiAlternatives для HTML-письма (если нужно)
def send_html_confirmation_email(user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    confirmation_link = f"http://yourdomain.com{reverse('confirm_email', kwargs={'uidb64': uid, 'token': token})}"

    subject = 'Подтверждение электронной почты'
    html_content = render_to_string('sign/confirm_email.html', {'confirmation_link': confirmation_link})

    msg = EmailMultiAlternatives(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_content, "text/html")  # добавляем html-содержимое
    msg.send()  # отправляем письмо


class CustomSignupView(SignupView):
    def form_valid(self, form):
        response = super().form_valid(form)
        # Дополнительная логика после успешной регистрации
        return response


# Ваши существующие views
@login_required
def upgrade_me(request):
    user = request.user
    authors_group = Group.objects.get(name='authors')
    if not request.user.groups.filter(name='authors').exists():
        authors_group.user_set.add(user)

        # Отправляем письмо о получении статуса автора
        send_author_welcome_email(user)

    return redirect('/')


def send_author_welcome_email(user):
    context = {
        'user': user,
        'site_url': settings.SITE_URL,
    }

    subject = 'Поздравляем! Вы стали автором'
    html_content = render_to_string('protect/index.html', context)

    msg = EmailMultiAlternatives(
        subject,
        '',
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()