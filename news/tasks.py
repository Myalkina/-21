from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from .models import Subscription, Post


def send_weekly_digest():
    """
    Отправка еженедельной рассылки подписчикам
    """
    print("=== ЗАПУСК ЕЖЕНЕДЕЛЬНОЙ РАССЫЛКИ ===")

    # Определяем период - последние 7 дней
    week_ago = timezone.now() - timedelta(days=7)

    # Получаем все активные подписки
    subscriptions = Subscription.objects.select_related('user', 'category').all()

    sent_count = 0
    error_count = 0

    for subscription in subscriptions:
        user = subscription.user
        category = subscription.category

        if not user.email:
            print(f"У пользователя {user.username} нет email, пропускаем")
            continue

        # Получаем новые статьи за неделю в этой категории
        new_posts = Post.objects.filter(
            postCategory=category,
            dateCreation__gte=week_ago
        ).select_related('author').order_by('-dateCreation')

        if not new_posts.exists():
            print(f"Нет новых статей в категории {category.name}")
            continue

        # Формируем email
        subject = f'📰 Еженедельная рассылка: новые статьи в категории "{category.name}"'

        html_message = render_to_string('account/email/weekly_digest.html', {
            'user': user,
            'category': category,
            'posts': new_posts,
            'site_url': settings.SITE_URL,
            'week_ago': week_ago,
        })

        text_message = f'''Еженедельная рассылка новых статей в категории "{category.name}"

За последнюю неделю опубликовано {new_posts.count()} новых статей:

'''

        for post in new_posts:
            text_message += f"• {post.title} ({post.dateCreation.strftime('%d.%m.%Y')})\n"
            text_message += f"  {settings.SITE_URL}/news/{post.id}/\n\n"

        text_message += f'''
---
Чтобы отписаться от рассылки, перейдите по ссылке: 
{settings.SITE_URL}/news/unsubscribe/{category.id}/
'''

        try:
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            sent_count += 1
            print(f"✓ Отправлено {user.email} - {new_posts.count()} статей")

        except Exception as e:
            error_count += 1
            print(f"✗ Ошибка отправки для {user.email}: {e}")

    print(f"=== РАССЫЛКА ЗАВЕРШЕНА ===")
    print(f"Успешно отправлено: {sent_count}")
    print(f"Ошибок: {error_count}")


@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    Удаление старых записей выполненных заданий (старше 7 дней)
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


def start_scheduler():
    """
    Запуск планировщика задач
    """
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Добавляем задачу еженедельной рассылки (каждое воскресенье в 09:00)
    scheduler.add_job(
        send_weekly_digest,
        trigger=CronTrigger(day_of_week="sun", hour=9, minute=0),
        id="weekly_digest",
        max_instances=1,
        replace_existing=True,
    )
    print("Добавлена задача еженедельной рассылки: воскресенье 09:00")

    # Добавляем задачу очистки старых записей (каждый день в 00:00)
    scheduler.add_job(
        delete_old_job_executions,
        trigger=CronTrigger(hour=0, minute=0),
        id="delete_old_job_executions",
        max_instances=1,
        replace_existing=True,
    )
    print("Добавлена задача очистки старых записей: ежедневно 00:00")

    try:
        print("Запуск планировщика...")
        scheduler.start()
    except KeyboardInterrupt:
        print("Остановка планировщика...")
        scheduler.shutdown()