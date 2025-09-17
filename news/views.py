from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Post, Category, Subscription, Author
from django.db.models import Q
from .forms import PostForm
from .filters import PostFilter
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

class PostList(ListView):
    model = Post
    ordering = '-dateCreation'
    template_name = 'posts.html'
    context_object_name = 'newsposts'
    paginate_by = 10


    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = PostFilter(self.request.GET, queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем в контекст объект фильтрации.
        context['filterset'] = self.filterset
        context['categories'] = Category.objects.all()

        # Добавляем информацию о подписках пользователя
        if self.request.user.is_authenticated:
            context['user_subscriptions'] = Subscription.objects.filter(
                user=self.request.user
            ).values_list('category_id', flat=True)
        return context


class PostDetail(DetailView):
    model = Post
    template_name = 'post.html'
    context_object_name = 'newspost'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_now'] = timezone.now()
        context['next_sale'] = None

        # Добавляем информацию о подписках пользователя
        if self.request.user.is_authenticated:
            context['user_subscriptions'] = Subscription.objects.filter(
                user=self.request.user
            ).values_list('category_id', flat=True)

        return context

    def get_queryset(self):
        return Post.objects.filter(Q(categoryType='NW') | Q(categoryType='AR'))


@login_required
def subscribe_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    subscription, created = Subscription.objects.get_or_create(
        user=request.user,
        category=category
    )

    if created:
        message = f'Вы успешно подписались на категорию "{category.name}"'
    else:
        message = f'Вы уже подписаны на категорию "{category.name}"'

    return HttpResponseRedirect(
        reverse('post_list') + f'?message={message}'
    )


@login_required
def unsubscribe_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    Subscription.objects.filter(
        user=request.user,
        category=category
    ).delete()

    message = f'Вы отписались от категории "{category.name}"'
    return HttpResponseRedirect(
        reverse('post_list') + f'?message={message}'
    )


class CategoryListView(ListView):
    model = Category
    template_name = 'categories.html'
    context_object_name = 'categories'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['user_subscriptions'] = Subscription.objects.filter(
                user=self.request.user
            ).values_list('category_id', flat=True)
        return context


# Функция для отправки email уведомлений (вызывается при создании поста)
def send_new_post_notification(post):
    print(f"=== ОТПРАВКА УВЕДОМЛЕНИЙ ДЛЯ ПОСТА: {post.title} ===")

    try:
        categories = post.postCategory.all()
        print(f"Категории поста: {[c.name for c in categories]}")

        for category in categories:
            subscribers = Subscription.objects.filter(category=category)
            print(f"Категория '{category.name}': {subscribers.count()} подписчиков")

            for subscription in subscribers:
                user = subscription.user
                print(f"Отправка для: {user.username} ({user.email})")

                if user.email:
                    subject = f'Новая статья в категории {category.name}'

                    # Создаем HTML сообщение
                    html_message = render_to_string('account/email/new_post_notification.html', {
                        'post': post,
                        'category': category,
                        'user': user,
                        'site_url': settings.SITE_URL,
                    })

                    # Текстовое сообщение
                    text_message = f'''
                        Новая статья: {post.title}
                        Категория: {category.name}

                        {post.preview()}

                        Читать полную статью: {settings.SITE_URL}/news/{post.id}/
                        '''

                    # Отправляем email
                    send_mail(
                        subject=subject,
                        message=text_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        html_message=html_message,
                    )
                    print(f"Email отправлен на {user.email}")
                else:
                    print(f"У пользователя {user.username} нет email")

    except Exception as e:
        print(f"Ошибка отправки уведомлений: {e}")


class PostCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    form_class = PostForm
    model = Post
    template_name = 'post_edit.html'
    success_url = reverse_lazy('post_list')
    permission_required = 'news.add_post'

    def form_valid(self, form):
        post = form.save(commit=False)
        post.quantity = 13
        # Убедитесь, что автор устанавливается правильно
        try:
            post.author = self.request.user.author
        except Author.DoesNotExist:
            # Если у пользователя нет Author, создаем его
            author = Author.objects.create(authorUser=self.request.user)
            post.author = author

        # Сохраняем пост
        response = super().form_valid(form)

        print("=== ВЫЗОВ ФУНКЦИИ ОТПРАВКИ УВЕДОМЛЕНИЙ ===")

        # Отправляем уведомления после успешного создания поста
        send_new_post_notification(self.object)

        return response

class PostUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    form_class = PostForm
    model = Post
    template_name = 'post_edit.html'
    success_url = reverse_lazy('post_list')
    permission_required = 'news.change_post'


class PostDelete(DeleteView):
    model = Post
    template_name = 'post_delete.html'
    success_url = reverse_lazy('post_list')
