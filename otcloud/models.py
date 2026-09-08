from django.db import models
from django.urls import reverse
from django.utils import timezone


class BlogPost(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True,
                            help_text='URL segment, e.g. "signs-of-speech-delay". Auto-filled from the title.')
    author = models.CharField(max_length=120, default='OT Cloud Team')
    cover_image = models.ImageField(upload_to='blog/', blank=True, null=True)
    excerpt = models.TextField(max_length=300, blank=True,
                               help_text='Short summary shown on the blog list (optional).')
    body = models.TextField(help_text='Write the article. Blank lines start new paragraphs.')
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
