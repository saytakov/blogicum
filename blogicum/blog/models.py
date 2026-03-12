from django.contrib.auth import get_user_model
from django.db import models

from core.models import AppConfig

LENGTH_TITLE = 256
COUNT_CHARS_TITLE = 30

User = get_user_model()


class Category(AppConfig):
    """Модель категорий"""

    title = models.CharField(
        max_length=LENGTH_TITLE,
        verbose_name='Заголовок',
    )
    description = models.TextField(
        verbose_name='Описание',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text=(
            'Идентификатор страницы для URL; разрешены символы латиницы, '
            'цифры, дефис и подчёркивание.'
        ),
    )

    class Meta:
        verbose_name: str = 'категория'
        verbose_name_plural: str = 'Категории'

    def __str__(self) -> str:
        return self.title


class Location(AppConfig):
    """Модель локаций"""

    name = models.CharField(
        max_length=LENGTH_TITLE,
        verbose_name='Название места',
    )

    class Meta:
        verbose_name: str = 'местоположение'
        verbose_name_plural: str = 'Местоположения'

    def __str__(self) -> str:
        return self.name


class Post(AppConfig):
    """Модель постов"""

    title = models.CharField(
        max_length=LENGTH_TITLE,
        verbose_name='Заголовок',
    )
    text = models.TextField(
        verbose_name='Текст',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем — '
            'можно делать отложенные публикации.'
        ),
    )
    image = models.ImageField(
        verbose_name='Фотография',
        upload_to='post_images',
        blank=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор публикации',
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
        verbose_name='Местоположение',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts',
        verbose_name='Категория',
    )

    class Meta:
        verbose_name: str = 'публикация'
        verbose_name_plural: str = 'Публикации'

    def __str__(self) -> str:
        return self.title


class Comment(AppConfig):

    text = models.TextField(
        verbose_name='Текст',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='comments',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Пост',
        related_name='comments',
    )

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'

        ordering = ('-created_at',)

    def __str__(self):
        return self.text[:COUNT_CHARS_TITLE] + '...'
