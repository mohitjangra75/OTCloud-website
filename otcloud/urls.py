"""
URL configuration for otcloud project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .sitemaps import BlogSitemap, StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('services/occupational-therapy/', views.service_ot, name='service_ot'),
    path('services/speech-therapy/', views.service_speech, name='service_speech'),
    path('services/early-intervention/', views.service_early, name='service_early'),
    path('services/special-education/', views.service_se, name='service_se'),
    path('services/child-psychology/', views.service_psychology, name='service_psychology'),
    path('concerns/', views.concerns, name='concerns'),
    path('assessment/', views.assessment, name='assessment'),
    path('resources/', views.resources, name='resources'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('contact/', views.contact, name='contact'),
    path('milestone-check/', views.milestone_check, name='milestone_check'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]

# Serve user-uploaded media during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
