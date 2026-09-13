import html

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe


class BlogPost(models.Model):
    """A post in the blog library. Everything published here is either a short
    ARTICLE (700-1,200 words, one question) or a longer GUIDE (1,500+ words,
    a whole topic) — both live under /blog/, never as separate site sections."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    KIND_CHOICES = [
        ('article', 'Article — short, answers one question'),
        ('guide', 'Guide — longer, covers a whole topic'),
    ]
    # Topics parents browse by. The key doubles as the /blog/topic/<slug>/ URL.
    CATEGORY_CHOICES = [
        ('child-development', 'Child Development'),
        ('occupational-therapy', 'Occupational Therapy'),
        ('speech-language', 'Speech & Language'),
        ('sensory-processing', 'Sensory Processing'),
        ('behaviour', 'Behaviour & Emotional Regulation'),
        ('learning', 'Learning & School Readiness'),
        ('parent-guides', 'Parent Guides'),
    ]
    SERVICE_CHOICES = [
        ('service_ot', 'Occupational Therapy'),
        ('service_speech', 'Speech and Language Therapy'),
        ('service_early', 'Early Intervention'),
        ('service_se', 'Special Education'),
        ('service_psychology', 'Child Psychology'),
        ('service_physio', 'Child Physiotherapy'),
    ]
    SERVICE_BLURBS = {
        'service_ot': 'Learn how occupational therapy may support sensory regulation, motor skills '
                      'and participation in everyday activities.',
        'service_speech': 'Learn how speech and language therapy may support understanding, '
                          'expression and social communication.',
        'service_early': 'Learn how early intervention may support communication, play, movement '
                         'and foundational learning skills in the early years.',
        'service_se': 'Learn how special education support may help with learning, pre-academic '
                      'skills and classroom participation.',
        'service_psychology': 'Learn how psychology and behaviour support may help with emotions, '
                              'attention, behaviour and everyday routines.',
        'service_physio': 'Learn how child physiotherapy may support strength, balance, coordination, '
                          'mobility and everyday movement.',
    }

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True,
                            help_text='URL segment, e.g. "signs-of-speech-delay". Auto-filled from the title.')
    kind = models.CharField('Type', max_length=10, choices=KIND_CHOICES, default='article')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='child-development',
                                help_text='Topic this post is filed under.')
    author = models.CharField(max_length=120, default='OT Cloud Team')
    cover_image = models.ImageField(upload_to='blog/', blank=True, null=True)
    excerpt = models.TextField(max_length=300, blank=True,
                               help_text='Two-line summary shown on cards and as the article introduction.')
    body = models.TextField(help_text='Blank lines start new paragraphs. Start a line with "## " for a '
                                      'section heading, "### " for a sub-heading and "- " for a bullet.')
    key_takeaways = models.TextField(blank=True,
                                     help_text='One takeaway per line. Shown in a highlighted box under the introduction.')
    reading_time = models.PositiveSmallIntegerField(default=0,
                                                    help_text='Minutes. Leave at 0 to calculate it from the body.')
    start_here = models.BooleanField(default=False,
                                     help_text='Feature this post in the "Start Here" row at the top of the blog.')
    from_therapy_team = models.BooleanField('Insight from the therapy team', default=False,
                                            help_text='Show this post under "Insights from OTCloud".')
    related_concern = models.CharField(max_length=60, blank=True,
                                       help_text='Concern to link at the end of the post, e.g. "Sensory Processing".')
    related_concern_note = models.CharField(max_length=220, blank=True,
                                            help_text='One line describing that concern (optional).')
    related_service = models.CharField(max_length=30, choices=SERVICE_CHOICES, blank=True,
                                       help_text='OTCloud service to link at the end of the post (optional).')
    views = models.PositiveIntegerField(default=0, editable=False,
                                        help_text='Read count — drives the "Parents Are Reading" row.')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(default=timezone.now)
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
    def is_guide(self):
        return self.kind == 'guide'

    @property
    def read_minutes(self):
        """Stated reading time, or a ~200 words-per-minute estimate."""
        if self.reading_time:
            return self.reading_time
        return max(1, round(len(self.body.split()) / 200))

    @property
    def takeaway_list(self):
        return [line.strip().lstrip('-').strip()
                for line in self.key_takeaways.splitlines() if line.strip()]

    @property
    def related_service_url(self):
        return reverse(self.related_service) if self.related_service else ''

    @property
    def related_service_blurb(self):
        return self.SERVICE_BLURBS.get(self.related_service, '')

    @property
    def body_html(self):
        """Render the body: paragraphs, "## " headings and "- " bullets.
        Everything is escaped first, so post content can never inject markup."""
        blocks, bullets = [], []

        def flush():
            if bullets:
                blocks.append('<ul>' + ''.join('<li>%s</li>' % b for b in bullets) + '</ul>')
                bullets.clear()

        for raw in self.body.splitlines():
            line = raw.strip()
            if not line:
                flush()
                continue
            if line.startswith('## '):
                flush()
                blocks.append('<h2>%s</h2>' % html.escape(line[3:].strip()))
            elif line.startswith('### '):
                flush()
                blocks.append('<h3>%s</h3>' % html.escape(line[4:].strip()))
            elif line.startswith('- '):
                bullets.append(html.escape(line[2:].strip()))
            else:
                blocks.append('<p>%s</p>' % html.escape(line))
        flush()
        return mark_safe(''.join(blocks))


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
