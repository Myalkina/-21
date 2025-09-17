from django.urls import path
from .views import PostList, PostDetail, PostCreate, PostUpdate, PostDelete, subscribe_category, unsubscribe_category, CategoryListView

urlpatterns = [
    path('', PostList.as_view(),name='post_list'),
    path('<int:pk>/', PostDetail.as_view(), name='post_detail'),
    path('create/', PostCreate.as_view(), name='post_create'),
    path('<int:pk>/update/', PostUpdate.as_view(), name='post_update'),
    path('<int:pk>/delete/', PostDelete.as_view(), name='post_delete'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('subscribe/<int:category_id>/', subscribe_category, name='subscribe_category'),
    path('unsubscribe/<int:category_id>/', unsubscribe_category, name='unsubscribe_category'),
    ]

