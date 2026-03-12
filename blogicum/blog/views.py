from typing import Any

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q, QuerySet
from django.db.models.base import Model as Model
from django.forms import BaseModelForm
from django.http import Http404, HttpRequest
from django.http.response import HttpResponseRedirect
from django.shortcuts import HttpResponse, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from .forms import CommentForm, PostForm, UserForm
from .models import Category, Comment, Post, User
from .utils import paginator_page

# Количество постов на странице
COUNT_POSTS = 10


class OnlyAuthorMixin(UserPassesTestMixin):
    """Является ли пользователь автором объекта."""

    def test_func(self) -> bool | None:
        return self.get_object().author == self.request.user


class IndexListView(ListView):
    """Главная страница. Опубликованные посты."""

    template_name = 'blog/index.html'
    paginate_by = COUNT_POSTS
    queryset = (
        Post.objects
        .order_by('-pub_date')
        .annotate(
            comment_count=Count(
                'comments',
                filter=(Q(comments__is_published=True))
            )
        )
        .select_related('author', 'location', 'category')
        .filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        )
    )


class ProfileDetailView(DetailView):
    """Личный кабинет пользователя."""

    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'blog/profile.html'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """
        Добавление постов в контекст.
        Автор страницы видит посты скрытые админом.
        Подключена пагинация.
        """
        context = super().get_context_data(**kwargs)
        user = self.object
        posts: QuerySet[Post] = user.posts.annotate(
            comment_count=Count(
                'comments',
                filter=(Q(comments__is_published=True))
            )
        ).order_by('-pub_date').select_related(
            'author', 'category', 'location'
        )
        if self.request.user != user:
            posts = posts.filter(
                Q(pub_date__lte=timezone.now())
                & Q(is_published=True)
                & Q(category__is_published=True)
            )
        context['page_obj'] = paginator_page(self.request, posts)
        return context


class ProfileUpdateView(UserPassesTestMixin, LoginRequiredMixin, UpdateView):
    """
    Страница для редактирования профиля.
    Доступна только хозяину профиля.
    """

    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def test_func(self) -> bool | None:
        """Является ли пользователь хозяином профиля."""
        return self.get_object() == self.request.user

    def get_success_url(self) -> str:
        """
        После удачного редактирования,
        перенаправлям на страницу личного кабинета.
        """
        return reverse(
            'blog:profile',
            kwargs={'username': self.get_object().username}
        )

    def get_object(self, queryset=None):
        """Получаем объект пользователя"""
        return self.request.user


class PostDetailView(UserPassesTestMixin, DetailView):
    """Страница для просмотра отдельного поста."""

    model = Post
    template_name = 'blog/detail.html'

    def test_func(self) -> bool | None:
        """
        Достоточно ли прав у пользователя на просмотр страницы.
        Доступ к невышедшему посту только у автора поста.
        Доступ к посту снятому админом есть только у автора поста.
        """
        object = self.get_object()
        return not (
            (object.author != self.request.user)
            and (
                (object.pub_date > timezone.now())
                or (not object.is_published)
                or (not object.category.is_published)
            ))

    def handle_no_permission(self) -> HttpResponseRedirect:
        """
        В случае не достаточности прав на просмотр страницы,
        вызываем ошибку 404, чтобы пользователь не знал, есть ли там пост.
        """
        raise Http404('Страницы не найдена.')

    def get_object(self, queryset: QuerySet[Any] | None = ...) -> Model:
        """Подключаем связные поля."""
        post_id = self.kwargs.get('post_id')
        if not hasattr(self, '_object'):
            try:
                self._object = Post.objects.select_related(
                    'author', 'location', 'category',
                ).get(pk=post_id)
            except ObjectDoesNotExist:
                raise Http404('Объект не найден.')
        return self._object

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Добавляем в контекст комментарии."""
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['form'] = CommentForm()
            comments = (
                Comment.objects.select_related(
                    'author'
                )
                .order_by('created_at')
                .filter(
                    Q(post=self.object)
                    & (
                        Q(is_published=True)
                        | (Q(is_published=False) & Q(author=self.request.user))
                    )
                )
            )
            context['comments'] = comments
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """
    Страница для создания поста.
    Доступна только зарегистрированным пользователям.
    """

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self) -> str:
        """
        После удачного создания,
        перенаправляем на страницу личного кабинета.
        """
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Добавляем к форме поле автора."""
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(OnlyAuthorMixin, LoginRequiredMixin, UpdateView):
    """
    Страница для редактирования поста.
    Доступна только автору поста.
    """

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    slug_field = 'id'
    slug_url_kwarg = 'post_id'

    def handle_no_permission(self) -> HttpResponseRedirect:
        """В случае нехватки прав, перенаправляем на страницу поста."""
        return redirect(
            'blog:post_detail',
            post_id=self.kwargs.get('post_id'),
            permanent=False
        )

    def get_success_url(self) -> str:
        """
        В случае удачного редактирования,
        перенаправялем на страцицу поста.
        """
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs.get('post_id')}
        )

    def get_object(self, queryset: QuerySet[Any] | None = ...) -> Model:
        """Подключаем связные поля к объекту поста."""
        if not hasattr(self, '_object'):
            post_id = self.kwargs.get('post_id')
            try:
                self._object = (
                    Post.objects
                    .select_related(
                        'author', 'category', 'location'
                    )
                    .get(id=post_id)
                )
            except ObjectDoesNotExist:
                raise Http404('Объект не найден.')
        return self._object


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    """
    Страница для удаления поста.
    Доступна только автору поста.
    """

    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def get_success_url(self) -> str:
        """
        В случае удачного удаления, перенаправляем
        на страницу личного кабинета.
        """
        user = self.request.user
        return reverse('blog:profile', kwargs={'username': user.username})

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Добавляем в контекст форму с данным удаляемого поста."""
        context = super().get_context_data(**kwargs)
        post = self.object
        form = PostForm(instance=post)
        context['form'] = form
        return context


@login_required
def add_comment(request: HttpRequest, post_id: int):
    """
    Дозаполнение полей комментария(пост, автор).
    Сохранене в БД.
    После сохранения перенаправляем на страницу поста.
    """
    form = CommentForm(request.POST)
    post = get_object_or_404(Post, pk=post_id)
    author = request.user
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = author
        comment.save()

    return redirect('blog:post_detail', post_id=post_id)


class CommentUpdateView(OnlyAuthorMixin, UpdateView):
    """
    Страница редактирования комменатрия.
    Доступна только автору комментария.
    """

    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'

    def get_success_url(self) -> str:
        """
        В случае удачного редактирования,
        перенаправляем на страницу поста.
        """
        post_id = self.kwargs.get('post_id')
        return reverse('blog:post_detail', kwargs={'post_id': post_id})


class CommentDelete(OnlyAuthorMixin, DeleteView):
    """
    Страница удаление комментария.
    Доступна только автору комментария.
    """

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self) -> str:
        """В случае удачного удаления, перенаправляем на страницу поста."""
        post_id = self.kwargs.get('post_id')
        return reverse('blog:post_detail', kwargs={'post_id': post_id})


class CategoryPostsListView(UserPassesTestMixin, DetailView):
    """Страница категории."""

    model = Category
    template_name = 'blog/category.html'
    slug_field = 'slug'
    slug_url_kwarg = 'category_slug'

    def test_func(self) -> bool | None:
        """Страница не доступна, если она снята с публикации."""
        return self.get_object().is_published

    def handle_no_permission(self) -> HttpResponseRedirect:
        raise Http404('Страница не найдена.')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Добавление постов в контекст.
        Подключение пагинации.
        """
        context = super().get_context_data(**kwargs)
        posts = (
            self.object.posts
            .annotate(
                comment_count=Count(
                    'comments',
                    filter=(Q(comments__is_published=True))
                )
            )
            .order_by('-pub_date')
            .select_related(
                'author', 'location'
            ).filter(
                pub_date__lte=timezone.now(),
                is_published=True,
                category__is_published=True,
            )
        )
        context['page_obj'] = paginator_page(self.request, posts)
        return context
