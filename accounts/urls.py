# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('home/', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('terms/', views.terms_view, name='terms'),
    path('profile-setup/', views.profile_setup, name='profile_setup'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('search/', views.search_view, name='search'),
    path('post/<int:post_id>/delete/', views.delete_post_view, name='delete_post'),
    path('comment/<int:comment_id>/delete/', views.delete_comment_view, name='delete_comment'),
    path('follow/<str:username>/', views.toggle_follow_view, name='toggle_follow'),
    path('friend-request/send/<str:username>/', views.send_friend_request, name='send_friend_request'),
    path('friend-request/unsend/<str:username>/', views.unsend_friend_request, name='unsend_friend_request'),
    path('friend-request/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friend-request/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('friend/unaccept/<str:username>/', views.unaccept_friend, name='unaccept_friend'),
    path('user/block/<str:username>/', views.block_user, name='block_user'),
    path('user/unblock/<str:username>/', views.unblock_user, name='unblock_user'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('messages/', views.inbox_view, name='inbox'),
    path('chat/<str:username>/', views.chat_view, name='chat'),
    path('message/<int:message_id>/delete/', views.delete_message_view, name='delete_message'),
]