# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from .forms import SignUpForm, UserProfileForm, LoginForm
from .models import UserProfile, Profile, Post, Comment, Follow, FriendRequest, Notification, Message, Block


# --- LANDING & PROFILE SETUP ---

def landing_page(request):
    """Landing Page which handles login via the index template form."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = LoginForm()

    return render(request, 'index.html', {'form': form})


@login_required
def profile_setup(request):
    """Step 2 profile configuration after signing up."""
    if request.method == "POST":
        user_age = request.POST.get('age')
        user_bio = request.POST.get('bio')
        
        profile, created = Profile.objects.get_or_create(user=request.user)
        if user_age:
            profile.age = int(user_age)
        profile.bio = user_bio
        profile.save()
        return redirect('home')

    return render(request, 'accounts/profile_setup.html')


# --- AUTHENTICATION VIEWS ---

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Safely ensure or update profile data with the selected community without unique constraint crashes
            Profile.objects.update_or_create(
                user=user,
                defaults={'community': form.cleaned_data.get('community')}
            )
            login(request, user)  # Auto-login after registration (Facebook style)
            return redirect('home')
    else:
        form = SignUpForm()
    
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('landing_page')


def terms_view(request):
    """Render the Terms and Conditions page."""
    return render(request, 'accounts/terms.html')


# --- FACEBOOK-STYLE FEED & SOCIAL VIEWS ---

@login_required
def home(request):
    """Main Feed Page (Newsfeed handling posts, visibility, and inline comments)."""
    if request.method == 'POST':
        # Handle new post submission with visibility, supporting both images and videos via request.FILES
        if 'content' in request.POST and 'post_id' not in request.POST:
            content = request.POST.get('content')
            media = request.FILES.get('media')
            visibility = request.POST.get('visibility', 'public')
            if content or media:
                Post.objects.create(author=request.user, content=content, media=media, visibility=visibility)
                return redirect('home')
                
        # Handle comment submission from feed items
        elif 'comment_content' in request.POST:
            post_id = request.POST.get('post_id')
            comment_text = request.POST.get('comment_content')
            post_obj = get_object_or_404(Post, id=post_id)
            if comment_text:
                Comment.objects.create(post=post_obj, author=request.user, content=comment_text)
                # Create a notification for post owner if someone else comments
                if post_obj.author != request.user:
                    Notification.objects.create(
                        recipient=post_obj.author,
                        sender=request.user,
                        notification_type='comment',
                        text=f"@{request.user.username} commented on your post."
                    )
            return redirect(f'/home/#post-{post_obj.id}')

    # Exclude posts from blocked users and respect privacy filters
    blocked_users = Block.objects.filter(Q(blocker=request.user) | Q(blocked=request.user))
    blocked_ids = set()
    for b in blocked_users:
        if b.blocker == request.user:
            blocked_ids.add(b.blocked.id)
        else:
            blocked_ids.add(b.blocker.id)

    following_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
    mutual_friends = [u for u in following_users if Follow.objects.filter(follower=u, following=request.user).exists()]

    posts = Post.objects.exclude(author__in=blocked_ids).filter(
        Q(visibility='public') |
        Q(author=request.user) |
        Q(visibility='friends', author__in=mutual_friends)
    ).distinct().order_by('-created_at')

    return render(request, 'accounts/feed.html', {'posts': posts})


@login_required
def profile_view(request, username):
    """View individual profile page with friend request, connection state, and block status checks."""
    profile_user = get_object_or_404(User, username=username)
    
    # Check if blocked either way
    is_blocked = Block.objects.filter(blocker=request.user, blocked=profile_user).exists()
    is_blocked_by = Block.objects.filter(blocker=profile_user, blocked=request.user).exists()

    user_posts = Post.objects.filter(author=profile_user).order_by('-created_at') if 'Post' in globals() else []
    
    is_following = False
    is_friend = False
    sent_request = None
    received_request = None

    if request.user != profile_user and not is_blocked and not is_blocked_by:
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
        
        # Check if they are mutual followers (friends)
        reverse_follow = Follow.objects.filter(follower=profile_user, following=request.user).exists()
        if is_following and reverse_follow:
            is_friend = True

        sent_request = FriendRequest.objects.filter(from_user=request.user, to_user=profile_user).first()
        received_request = FriendRequest.objects.filter(from_user=profile_user, to_user=request.user).first()

    context = {
        'profile_user': profile_user,
        'posts': user_posts,
        'is_following': is_following,
        'is_friend': is_friend,
        'sent_request': sent_request,
        'received_request': received_request,
        'is_blocked': is_blocked,
        'is_blocked_by': is_blocked_by,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def like_post(request, post_id):
    """Toggle like on a post and redirect back to its specific anchor."""
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
        if post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                notification_type='like',
                text=f"@{request.user.username} liked your post."
            )
    return redirect(f'/home/#post-{post.id}')


# --- SEARCH, PROFILE MANAGEMENT, DELETE, FOLLOW, FRIEND REQUESTS & MESSAGING VIEWS ---

@login_required
def search_view(request):
    """Search for other Berekum residents or filter posts by keywords, excluding blocked users."""
    query = request.GET.get('q', '')
    users = []
    posts = []
    if query:
        blocked_users = Block.objects.filter(Q(blocker=request.user) | Q(blocked=request.user))
        blocked_ids = set()
        for b in blocked_users:
            if b.blocker == request.user:
                blocked_ids.add(b.blocked.id)
            else:
                blocked_ids.add(b.blocker.id)

        users = User.objects.exclude(id__in=blocked_ids).filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(profile__community__icontains=query)
        ).distinct()
        posts = Post.objects.exclude(author__in=blocked_ids).filter(content__icontains=query)
    
    context = {'query': query, 'users': users, 'posts': posts}
    return render(request, 'accounts/search_results.html', context)


@login_required
def edit_profile_view(request):
    """Allow users to update bio, location, community, or avatar."""
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def delete_post_view(request, post_id):
    """Give users the ability to delete their own posts."""
    post = get_object_or_404(Post, id=post_id)
    if post.author == request.user:
        post.delete()
    return redirect('home')


@login_required
def delete_comment_view(request, comment_id):
    """Give users the ability to delete their own comments or comments on their posts."""
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author == request.user or comment.post.author == request.user:
        comment.delete()
    return redirect(f'/home/#post-{comment.post.id}')


@login_required
def toggle_follow_view(request, username):
    """Introduce friend/follow connection toggle and follow notification."""
    target_user = get_object_or_404(User, username=username)
    if target_user != request.user:
        follow_obj, created = Follow.objects.get_or_create(follower=request.user, following=target_user)
        if not created:
            follow_obj.delete()
        else:
            Notification.objects.create(
                recipient=target_user,
                sender=request.user,
                notification_type='follow',
                text=f"@{request.user.username} started following you."
            )
    return redirect('profile', username=username)


@login_required
def send_friend_request(request, username):
    """Send a peer-to-peer friend request."""
    target_user = get_object_or_404(User, username=username)
    if target_user != request.user:
        existing_request = FriendRequest.objects.filter(from_user=request.user, to_user=target_user).exists()
        reverse_request = FriendRequest.objects.filter(from_user=target_user, to_user=request.user).exists()
        
        if not existing_request and not reverse_request:
            FriendRequest.objects.create(from_user=request.user, to_user=target_user)
            Notification.objects.create(
                recipient=target_user,
                sender=request.user,
                notification_type='friend_request',
                text=f"@{request.user.username} sent you a friend request."
            )
    return redirect('profile', username=username)


@login_required
def unsend_friend_request(request, username):
    """Unsend an outgoing friend request."""
    target_user = get_object_or_404(User, username=username)
    FriendRequest.objects.filter(from_user=request.user, to_user=target_user).delete()
    return redirect('profile', username=username)


@login_required
def unaccept_friend(request, username):
    """Unfriend a user by clearing mutual follows and associated requests."""
    target_user = get_object_or_404(User, username=username)
    Follow.objects.filter(
        Q(follower=request.user, following=target_user) | Q(follower=target_user, following=request.user)
    ).delete()
    FriendRequest.objects.filter(
        Q(from_user=request.user, to_user=target_user) | Q(from_user=target_user, to_user=request.user)
    ).delete()
    return redirect('profile', username=username)


@login_required
def block_user(request, username):
    """Block a user and clear all relational links and requests."""
    target_user = get_object_or_404(User, username=username)
    if target_user != request.user:
        Block.objects.get_or_create(blocker=request.user, blocked=target_user)
        Follow.objects.filter(
            Q(follower=request.user, following=target_user) | Q(follower=target_user, following=request.user)
        ).delete()
        FriendRequest.objects.filter(
            Q(from_user=request.user, to_user=target_user) | Q(from_user=target_user, to_user=request.user)
        ).delete()
    return redirect('profile', username=username)


@login_required
def unblock_user(request, username):
    """Unblock a user."""
    target_user = get_object_or_404(User, username=username)
    Block.objects.filter(blocker=request.user, blocked=target_user).delete()
    return redirect('profile', username=username)


@login_required
def accept_friend_request(request, request_id):
    """Accept an incoming friend request and establish mutual follows."""
    friend_req = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    
    Follow.objects.get_or_create(follower=friend_req.from_user, following=request.user)
    Follow.objects.get_or_create(follower=request.user, following=friend_req.from_user)
    
    Notification.objects.create(
        recipient=friend_req.from_user,
        sender=request.user,
        notification_type='friend_accept',
        text=f"@{request.user.username} accepted your friend request."
    )
    friend_req.delete()
    return redirect('profile', username=friend_req.from_user.username)


@login_required
def reject_friend_request(request, request_id):
    """Reject or decline an incoming friend request."""
    friend_req = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_req.delete()
    return redirect('notifications')


@login_required
def notifications_view(request):
    """Introduce a lightweight notification system."""
    notifs = request.user.notifications.all()
    notifs.update(is_read=True)
    return render(request, 'accounts/notifications.html', {'notifications': notifs})


@login_required
def inbox_view(request):
    """Messaging system inbox listing other platform users with unread counts per chat, excluding blocked users."""
    blocked_users = Block.objects.filter(Q(blocker=request.user) | Q(blocked=request.user))
    blocked_ids = set()
    for b in blocked_users:
        if b.blocker == request.user:
            blocked_ids.add(b.blocked.id)
        else:
            blocked_ids.add(b.blocker.id)

    messages_qs = Message.objects.exclude(
        Q(sender__in=blocked_ids) | Q(receiver__in=blocked_ids)
    ).filter(Q(sender=request.user) | Q(receiver=request.user))
    
    partner_ids = set()
    for msg in messages_qs:
        if msg.sender == request.user:
            partner_ids.add(msg.receiver.id)
        else:
            partner_ids.add(msg.sender.id)
            
    partners = User.objects.filter(id__in=partner_ids)
    
    chat_list = []
    for partner in partners:
        unread_count = Message.objects.filter(sender=partner, receiver=request.user, is_read=False).count()
        chat_list.append({
            'partner': partner,
            'unread_count': unread_count,
        })
        
    context = {'chat_list': chat_list}
    return render(request, 'accounts/inbox.html', context)


@login_required
def chat_view(request, username):
    """Messaging system chat view with restriction logic, block checks, and delete support."""
    other_user = get_object_or_404(User, username=username)
    
    # Check if a block exists between users
    is_blocked = Block.objects.filter(
        Q(blocker=request.user, blocked=other_user) | Q(blocker=other_user, blocked=request.user)
    ).exists()
    if is_blocked:
        return redirect('inbox')

    # Automatically mark incoming unread messages from this partner as read
    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)

    # Check if current user and other user are friends (mutual follow)
    user_follows = Follow.objects.filter(follower=request.user, following=other_user).exists()
    other_follows = Follow.objects.filter(follower=other_user, following=request.user).exists()
    is_friend = user_follows and other_follows

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # If they are not friends, check if the user has already sent a message
            if not is_friend:
                sent_count = Message.objects.filter(sender=request.user, receiver=other_user).count()
                if sent_count >= 1:
                    return redirect('chat', username=username)

            Message.objects.create(sender=request.user, receiver=other_user, content=content)
            Notification.objects.create(
                recipient=other_user,
                sender=request.user,
                notification_type='message',
                text=f"@{request.user.username} sent you a message."
            )
            return redirect('chat', username=username)

    # Fetch messages visible to the current user (taking soft deletes into account)
    chat_messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user) & Q(is_deleted_by_sender=False)) |
        (Q(sender=other_user) & Q(receiver=request.user) & Q(is_deleted_by_receiver=False))
    ).order_by('timestamp')

    can_send = True
    if not is_friend:
        sent_count = Message.objects.filter(sender=request.user, receiver=other_user).count()
        if sent_count >= 1:
            can_send = False

    context = {
        'other_user': other_user, 
        'chat_messages': chat_messages,
        'can_send': can_send,
        'is_friend': is_friend
    }
    return render(request, 'accounts/chat.html', context)


@login_required
def delete_message_view(request, message_id):
    """Handle soft deletion or complete removal of a message."""
    msg = get_object_or_404(Message, id=message_id)
    if msg.sender == request.user:
        msg.is_deleted_by_sender = True
        msg.save()
    elif msg.receiver == request.user:
        msg.is_deleted_by_receiver = True
        msg.save()
    
    if msg.is_deleted_by_sender and msg.is_deleted_by_receiver:
        msg.delete()
        
    partner_username = msg.receiver.username if msg.sender == request.user else msg.sender.username
    return redirect('chat', username=partner_username)