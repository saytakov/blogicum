from django.urls import URLPattern, path
from django.views.generic import TemplateView

app_name: str = 'pages'

urlpatterns: list[URLPattern] = [
    path('about/',
         TemplateView.as_view(template_name='pages/about.html'),
         name='about'),
    path('rules/',
         TemplateView.as_view(template_name='pages/rules.html'),
         name='rules'),
]
