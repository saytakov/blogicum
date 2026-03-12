from typing import Any

from django.core.paginator import Page, Paginator
from django.db.models import QuerySet
from django.http import HttpRequest

COUNT_POSTS = 10


def paginator_page(
    request: HttpRequest,
    object_list: list[Any] | QuerySet[Any],
    per_page: int = COUNT_POSTS
) -> Page:
    """Подлкючение пагинации."""
    paginator = Paginator(object_list, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
