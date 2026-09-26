"""Simplify BlogPost: the body moves to the rich-text editor (HTML), the excerpt becomes
the SEO meta description, and the type / takeaways / placement / linked-page fields go."""
import html

import django.utils.timezone
import django_ckeditor_5.fields
from django.db import migrations, models


def _text_to_html(text):
    """The old body format: blank lines between paragraphs, "## " / "### " headings, "- " bullets."""
    blocks, bullets = [], []

    def flush():
        if bullets:
            blocks.append('<ul>' + ''.join('<li>%s</li>' % b for b in bullets) + '</ul>')
            bullets.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush()
        elif line.startswith('## '):
            flush()
            blocks.append('<h2>%s</h2>' % html.escape(line[3:].strip()))
        elif line.startswith('### '):
            flush()
            blocks.append('<h3>%s</h3>' % html.escape(line[4:].strip()))
        elif line.startswith('- '):
            bullets.append(html.escape(line[2:].strip()))
        else:
            flush()
            blocks.append('<p>%s</p>' % html.escape(line))
    flush()
    return ''.join(blocks)


def body_to_html(apps, schema_editor):
    BlogPost = apps.get_model('otcloud', 'BlogPost')
    for post in BlogPost.objects.all():
        body = _text_to_html(post.body)
        # Keep any written takeaways as an editable section at the top of the post.
        points = [line.strip().lstrip('-').strip() for line in post.key_takeaways.splitlines() if line.strip()]
        if points:
            body = ('<h2>Key Takeaways</h2><ul>'
                    + ''.join('<li>%s</li>' % html.escape(p) for p in points) + '</ul>' + body)
        post.body = body
        post.save(update_fields=['body'])


class Migration(migrations.Migration):

    dependencies = [
        ('otcloud', '0011_remove_parent_guides_category'),
    ]

    operations = [
        migrations.RunPython(body_to_html, migrations.RunPython.noop),
        migrations.RenameField('blogpost', 'excerpt', 'meta_description'),
        migrations.AlterField(
            model_name='blogpost',
            name='meta_description',
            field=models.CharField(blank=True, max_length=180, verbose_name='Meta description',
                                   help_text='One or two sentences (about 150–160 characters) shown in Google '
                                             'results and on blog cards. Leave blank to use the opening of the post.'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='meta_title',
            field=models.CharField(blank=True, max_length=70, verbose_name='SEO title',
                                   help_text='Title shown in Google results (up to about 60 characters). '
                                             'Leave blank to use the post title.'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='cover_image_alt',
            field=models.CharField(blank=True, max_length=150, verbose_name='Cover image description',
                                   help_text='Describe the image for screen readers and search engines. '
                                             'Leave blank to use the title.'),
        ),
        migrations.RemoveField('blogpost', 'kind'),
        migrations.RemoveField('blogpost', 'key_takeaways'),
        migrations.RemoveField('blogpost', 'reading_time'),
        migrations.RemoveField('blogpost', 'start_here'),
        migrations.RemoveField('blogpost', 'from_therapy_team'),
        migrations.RemoveField('blogpost', 'related_concern'),
        migrations.RemoveField('blogpost', 'related_concern_note'),
        migrations.RemoveField('blogpost', 'related_service'),
        migrations.AlterField(
            model_name='blogpost',
            name='body',
            field=django_ckeditor_5.fields.CKEditor5Field(),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='category',
            field=models.CharField(choices=[('child-development', 'Child Development'), ('occupational-therapy', 'Occupational Therapy'), ('speech-language', 'Speech & Language'), ('sensory-processing', 'Sensory Processing'), ('behaviour', 'Behaviour & Emotional Regulation'), ('learning', 'Learning & School Readiness')], default='child-development', max_length=30, verbose_name='Topic'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='cover_image',
            field=models.ImageField(blank=True, help_text='Shown on cards and when the post is shared. 1200 × 630 px works best.', null=True, upload_to='blog/'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='published_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Publish date'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='views',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
    ]
