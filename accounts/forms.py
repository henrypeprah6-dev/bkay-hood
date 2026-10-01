# accounts/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile, Profile, Post, Comment


class LoginForm(AuthenticationForm):
    """Custom login form to ensure username and password widgets have proper Tailwind styles and placeholders."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2.5 border rounded-lg focus:outline-none focus:border-brandPink bg-gray-50 text-sm',
            'placeholder': 'Enter your username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-2.5 border rounded-lg focus:outline-none focus:border-brandPink bg-gray-50 text-sm',
            'placeholder': 'Enter your password'
        })
    )


class SignUpForm(UserCreationForm):
    """Registration form tailored for Facebook-style sign up with updated Berekum communities."""
    first_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'Last name'})
    )
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'placeholder': 'Email address'})
    )

    # Updated Berekum communities with requested removals and additions
    BEREKUM_COMMUNITIES = [
        ('', 'Select your area / community in Berekum'),
        ('Adom', 'Adom'),
        ('Benkasa', 'Benkasa'),
        ('Berekum Central', 'Berekum Central'),
        ('Berekum Magazine', 'Berekum Magazine'),
        ('Biadan', 'Biadan'),
        ('Brenyekwa', 'Brenyekwa'),
        ('Domfete', 'Domfete'),
        ('Fetentaa', 'Fetentaa'),
        ('Jamdede', 'Jamdede'),
        ('Jinijini', 'Jinijini'),
        ('Kato', 'Kato'),
        ('Koraso', 'Koraso'),
        ('Kyeribaa', 'Kyeribaa'),
        ('Mpatapo', 'Mpatapo'),
        ('Mpatasie', 'Mpatasie'),
        ('Namasua', 'Namasua'),
        ('Nanasuano', 'Nanasuano'),
        ('Nsapor', 'Nsapor'),
        ('Nyame Bekyere', 'Nyame Bekyere'),
        ('Senase', 'Senase'),
        ('Sofo Kyere', 'Sofo Kyere'),
    ]

    community = forms.ChoiceField(
        choices=BEREKUM_COMMUNITIES,
        required=True,
        widget=forms.Select()
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply standard form styling across input fields
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full p-2.5 border rounded-lg focus:outline-none focus:border-brandPink'
            })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Safely update or create the profile to prevent race conditions with signals.py
            Profile.objects.update_or_create(
                user=user,
                defaults={'community': self.cleaned_data.get('community')}
            )
        return user


class UserProfileForm(forms.ModelForm):
    """Form to collect and update user profile details (Avatar, Bio, Location, Community)."""
    
    BEREKUM_COMMUNITIES = [
        ('', 'Select your area / community in Berekum'),
        ('Adom', 'Adom'),
        ('Benkasa', 'Benkasa'),
        ('Berekum Central', 'Berekum Central'),
        ('Berekum Magazine', 'Berekum Magazine'),
        ('Biadan', 'Biadan'),
        ('Brenyekwa', 'Brenyekwa'),
        ('Domfete', 'Domfete'),
        ('Fetentaa', 'Fetentaa'),
        ('Jamdede', 'Jamdede'),
        ('Jinijini', 'Jinijini'),
        ('Kato', 'Kato'),
        ('Koraso', 'Koraso'),
        ('Kyeribaa', 'Kyeribaa'),
        ('Mpatapo', 'Mpatapo'),
        ('Mpatasie', 'Mpatasie'),
        ('Namasua', 'Namasua'),
        ('Nanasuano', 'Nanasuano'),
        ('Nsapor', 'Nsapor'),
        ('Nyame Bekyere', 'Nyame Bekyere'),
        ('Senase', 'Senase'),
        ('Sofo Kyere', 'Sofo Kyere'),
    ]

    community = forms.ChoiceField(
        choices=BEREKUM_COMMUNITIES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full p-2.5 border rounded-lg focus:outline-none focus:border-brandPink'
        })
    )

    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'location', 'community']
        widgets = {
            'bio': forms.Textarea(attrs={
                'placeholder': 'Tell your community about yourself...',
                'rows': 3,
                'class': 'w-full p-2.5 border rounded-lg focus:outline-none focus:border-brandPink resize-none'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border rounded-lg focus:outline-none focus:border-brandPink'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'text-xs text-gray-500 w-full p-2 border rounded-lg'
            })
        }


class PostForm(forms.ModelForm):
    """Form for creating newsfeed posts with text content and optional image uploads."""
    class Meta:
        model = Post
        fields = ['content', 'image']
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': "What's on your mind?",
                'rows': 2,
                'class': 'w-full bg-gray-100 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-brandPink resize-none'
            }),
            'image': forms.FileInput(attrs={
                'class': 'text-xs text-gray-500'
            })
        }


class CommentForm(forms.ModelForm):
    """Form for publishing comments on feed posts."""
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'placeholder': 'Write a comment...',
                'class': 'w-full bg-gray-100 rounded-full px-4 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brandPink'
            })
        }