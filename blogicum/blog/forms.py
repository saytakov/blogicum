from django.forms import ModelForm
from django.forms.widgets import DateTimeInput

from .models import Comment, Post, User


class UserForm(ModelForm):
    """Форма для редкатирования полей пользователя."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')


class PostForm(ModelForm):
    """Форма для создания, редактирования, удаления полей поста."""

    class Meta:
        model = Post
        fields = ('title', 'text', 'pub_date', 'image', 'location', 'category')
        widgets = {
            'pub_date': DateTimeInput(
                attrs={'type': 'datetime-local'},
                format="%Y-%m-%d %H:%M:%S"
            )
        }


class CommentForm(ModelForm):
    """Форма для создания, редактирования, удаления полей комментария."""

    class Meta:
        model = Comment
        fields = ('text', )
