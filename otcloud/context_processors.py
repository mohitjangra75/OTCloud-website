from urllib.parse import quote

from django.conf import settings


def site_contact(request):
    """Expose clinic contact details + SEO helpers to all templates."""
    c = settings.SITE_CONTACT
    whatsapp_url = (
        f"https://api.whatsapp.com/send?phone={c['whatsapp_number']}"
        f"&text={quote(c['whatsapp_message'])}"
    )
    return {
        'site_name': settings.SITE_NAME,
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
