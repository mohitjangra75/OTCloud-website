from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import BlogPost


class StaticViewSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.7
    protocol = 'https'

    def items(self):
        return ['home', 'about', 'services', 'service_ot', 'service_speech', 'service_early',
                'service_se', 'service_psychology', 'service_physio', 'concerns', 'assessment', 'resources',
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


class BlogTopicSitemap(Sitemap):
    """One entry per blog topic listing, e.g. /blog/topic/sensory-processing/."""
    changefreq = 'weekly'
    priority = 0.5
    protocol = 'https'

    def items(self):
        return [key for key, _label in BlogPost.CATEGORY_CHOICES]

    def location(self, topic):
        return reverse('blog_topic', args=[topic])
