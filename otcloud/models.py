import html

import nh3
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator
from django_ckeditor_5.fields import CKEditor5Field

# nh3's safe defaults, plus target on links so the editor's "open in new tab" survives cleaning.
BODY_ATTRIBUTES = {**nh3.ALLOWED_ATTRIBUTES, 'a': nh3.ALLOWED_ATTRIBUTES.get('a', set()) | {'target'}}


class BlogPost(models.Model):
    """A post in the blog library, filed under one topic and written in the rich-text editor."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    # Editor classes kept when the body is cleaned: image alignment and figure types.
    BODY_CLASSES = {'figure': {'image', 'table', 'image-style-align-left', 'image-style-align-center',
                               'image-style-align-right', 'image-style-side'}}
    # Topics parents browse by. The key doubles as the /blog/topic/<slug>/ URL.
    CATEGORY_CHOICES = [
        ('child-development', 'Child Development'),
        ('occupational-therapy', 'Occupational Therapy'),
        ('speech-language', 'Speech & Language'),
        ('sensory-processing', 'Sensory Processing'),
        ('behaviour', 'Behaviour & Emotional Regulation'),
        ('learning', 'Learning & School Readiness'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True,
                            help_text='URL segment, e.g. "signs-of-speech-delay". Auto-filled from the title.')
    category = models.CharField('Topic', max_length=30, choices=CATEGORY_CHOICES, default='child-development')
    author = models.CharField(max_length=120, default='OT Cloud Team')
    cover_image = models.ImageField(upload_to='blog/', blank=True, null=True,
                                    help_text='Shown on cards and when the post is shared. 1200 × 630 px works best.')
    cover_image_alt = models.CharField('Cover image description', max_length=150, blank=True,
                                       help_text='Describe the image for screen readers and search engines. '
                                                 'Leave blank to use the title.')
    body = CKEditor5Field(config_name='blog')

    # SEO
    meta_title = models.CharField('SEO title', max_length=70, blank=True,
                                  help_text='Title shown in Google results (up to about 60 characters). '
                                            'Leave blank to use the post title.')
    meta_description = models.CharField('Meta description', max_length=180, blank=True,
                                        help_text='One or two sentences (about 150–160 characters) shown in Google '
                                                  'results and on blog cards. Leave blank to use the opening of the post.')

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField('Publish date', default=timezone.now)
    views = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog_detail', args=[self.slug])

    def get_category_url(self):
        return reverse('blog_topic', args=[self.category])

    @property
    def plain_text(self):
        # Space before each tag so words either side of one (e.g. "</li><li>") stay apart.
        return html.unescape(strip_tags(self.body.replace('<', ' <')))

    @property
    def summary(self):
        """Card and search-result summary: the meta description, else the post's opening."""
        return self.meta_description or Truncator(' '.join(self.plain_text.split())).chars(160)

    @property
    def seo_title(self):
        return self.meta_title or self.title

    @property
    def image_alt(self):
        return self.cover_image_alt or self.title

    @property
    def read_minutes(self):
        """About 200 words a minute."""
        return max(1, round(len(self.plain_text.split()) / 200))

    @property
    def body_html(self):
        """The editor's HTML, cleaned so only formatting tags survive (no scripts or inline handlers)."""
        return mark_safe(nh3.clean(self.body, attributes=BODY_ATTRIBUTES, allowed_classes=self.BODY_CLASSES))


class AssessmentRequest(models.Model):
    CONCERN_CHOICES = [
        ('speech', 'Speech & Language'),
        ('sensory', 'Sensory Processing'),
        ('motor', 'Motor Skills'),
        ('social', 'Social Development'),
        ('academic', 'Academic Performance'),
    ]
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('scheduled', 'Scheduled'),
        ('closed', 'Closed'),
    ]

    child_name = models.CharField(max_length=120)
    child_age = models.CharField('Child age', max_length=40, blank=True,
                                 help_text='As given by the parent, e.g. "4 years 6 months".')
    child_dob = models.DateField('Child date of birth', null=True, blank=True)
    parent_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    area_of_concern = models.CharField(max_length=20, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.child_name} — {self.parent_name} ({self.created_at:%d %b %Y})'


class AppointmentEnquiry(models.Model):
    CONCERN_CHOICES = [
        ('speech', 'Speech & Language'),
        ('ot', 'Occupational Therapy (Sensory/Motor)'),
        ('behavior', 'Behavioral Concerns'),
        ('autism', 'Autism Spectrum / Neurodiversity'),
        ('attention', 'Attention & Focus (ADHD)'),
        ('general', 'General Developmental Milestone Check'),
    ]
    CONTACT_CHOICES = [('phone', 'Phone'), ('whatsapp', 'WhatsApp')]
    TIME_CHOICES = [
        ('morning', 'Morning (9am - 12pm)'),
        ('afternoon', 'Afternoon (12pm - 4pm)'),
        ('evening', 'Evening (4pm - 7pm)'),
    ]
    STATUS_CHOICES = [('new', 'New'), ('contacted', 'Contacted'), ('closed', 'Closed')]

    parent_name = models.CharField(max_length=120)
    child_name = models.CharField(max_length=120)
    child_age = models.CharField(max_length=40, blank=True)
    phone = models.CharField(max_length=30)
    area_of_concern = models.CharField(max_length=20, blank=True)
    contact_method = models.CharField(max_length=10, choices=CONTACT_CHOICES, blank=True)
    preferred_time = models.CharField(max_length=12, choices=TIME_CHOICES, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Appointment enquiries'

    def __str__(self):
        return f'{self.child_name} — {self.parent_name} ({self.created_at:%d %b %Y})'


class NewsletterSignup(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    message = models.TextField()
    handled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.created_at:%d %b %Y})'


class MilestoneEnquiry(models.Model):
    """Contact details captured after a parent completes the home-page milestone check."""
    STATUS_CHOICES = [('new', 'New'), ('contacted', 'Contacted'), ('closed', 'Closed')]

    parent_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    child_age = models.CharField(max_length=60, blank=True,
                                 help_text='Age band the parent selected in the milestone check.')
    milestones_done = models.PositiveSmallIntegerField(default=0)
    milestones_total = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Milestone enquiries'

    def __str__(self):
        return f'{self.parent_name} — {self.child_age or "age not set"} ({self.created_at:%d %b %Y})'

    @property
    def not_yet(self):
        return max(self.milestones_total - self.milestones_done, 0)
