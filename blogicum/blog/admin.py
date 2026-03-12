from django.contrib import admin

from .models import Category, Comment, Location, Post

admin.site.empty_value_display = 'Не задано'


class PostInline(admin.TabularInline):
    model = Post
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'created_at',)
    list_display_links = ('title',)
    list_editable = ('is_published',)
    list_filter = ('is_published', 'created_at',)
    search_fields = ('title',)
    inlines = (PostInline,)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published', 'created_at',)
    list_display_links = ('name',)
    list_editable = ('is_published',)
    list_filter = ('is_published', 'created_at',)
    search_fields = ('name',)
    inlines = (PostInline,)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'pub_date', 'author', 'location', 'category', 'is_published',
        'created_at',
    )
    list_display_links = ('title',)
    list_editable = ('location', 'category', 'is_published', 'pub_date',)
    list_filter = (
        'pub_date', 'location', 'category', 'is_published', 'created_at',
    )
    search_fields = ('title',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at', 'is_published', 'text')
    search_fields = ('text', 'post', 'author')
    list_editable = ('is_published',)
    list_filter = ('is_published', 'author', 'created_at',)
