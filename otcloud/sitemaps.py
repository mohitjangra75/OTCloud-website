from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import BlogPost


class StaticViewSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.7
    protocol = 'https'

    def items(self):
        return ['home', 'about', 'services', 'service_ot', 'service_speech', 'service_early',
                'service_se', 'service_psychology', 'concerns', 'assessment', 'resources',
                'blog_list', 'contact', 'milestone_check', 'privacy', 'terms']

    def location(self, item):
        return reverse(item)

    def priority_for(self, item):
        return 1.0 if item == 'home' else 0.7


class BlogSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6
    protocol = 'https'

    def items(self):
        return BlogPost.objects.filter(status='published')

    def lastmod(self, obj):
        return obj.updated_at
