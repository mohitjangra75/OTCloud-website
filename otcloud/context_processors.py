import hashlib
from urllib.parse import quote

from django.conf import settings


def _announcement():
    """Announcement dict with a dismiss key derived from its content, so editing
    the text automatically re-shows the bar to visitors who dismissed the old one."""
    ann = getattr(settings, 'SITE_ANNOUNCEMENT', None)
    if not ann or not ann.get('enabled'):
        return ann
    sig = f"{ann.get('text', '')}|{ann.get('link_text', '')}|{ann.get('link_url', '')}"
    key = hashlib.md5(sig.encode('utf-8')).hexdigest()[:10]
    return {**ann, 'key': key}


def site_contact(request):
    """Expose clinic contact details + SEO helpers to all templates."""
    c = settings.SITE_CONTACT
    whatsapp_url = (
        f"https://api.whatsapp.com/send?phone={c['whatsapp_number']}"
        f"&text={quote(c['whatsapp_message'])}"
    )
    return {
        'site_name': settings.SITE_NAME,
        'announcement': _announcement(),
        'site_phone_display': c['phone_display'],
        'site_tel': c['tel'],
        'site_email': c['email'],
        'site_address': c['address'],
        'site_whatsapp_url': whatsapp_url,
        'site_facebook': c['facebook'],
        'site_youtube': c['youtube'],
        'site_instagram': c['instagram'],
        # Structured address (SEO / JSON-LD)
        'site_street': c['street'],
        'site_locality': c['locality'],
        'site_region': c['region'],
        'site_postal_code': c['postal_code'],
        'site_country': c['country'],
        # Absolute canonical URL for the current page (no query string)
        'canonical_url': request.build_absolute_uri(request.path),
    }
