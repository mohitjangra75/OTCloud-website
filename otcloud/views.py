from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import Truncator


from .forms import AppointmentEnquiryForm, AssessmentRequestForm, ContactForm
from .models import BlogPost


def _notify(subject, body, reply_to=None):
    """Email a notification to the clinic inbox. Never breaks the request flow."""
    EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.NOTIFY_EMAIL],
        reply_to=[reply_to] if reply_to else None,
    ).send(fail_silently=True)


SIGNS = [
    ('Speech and Communication', 'Difficulty using words, expressing needs or understanding instructions.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'),
    ('Social Interaction', 'Limited eye contact, shared play, response to name or interaction with others.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>'),
    ('Sensory Processing', 'Strong or unusual reactions to sounds, touch, movement, textures or crowded environments.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7"/><path d="M2 12s3 7 10 7 10-7 10-7"/><circle cx="12" cy="12" r="2"/></svg>'),
    ('Attention and Regulation', 'Difficulty staying focused, sitting for activities, following instructions or regulating activity levels.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1"/></svg>'),
    ('Behaviour and Emotions', 'Frequent meltdowns, rigid routines, difficulty managing frustration or challenges with transitions.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M16 16s-1.5-2-4-2-4 2-4 2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>'),
    ('Learning and School Readiness', 'Difficulty with early concepts, writing readiness, classroom participation or following routines.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>'),
    ('Movement and Coordination', 'Challenges with balance, posture, walking, running, hand skills or coordinated movement.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="1"/><path d="M9 20l3-6 3 6"/><path d="M6 8l6 2 6-2"/><path d="M12 10v4"/></svg>'),
    ('Daily Independence', 'Difficulty with dressing, feeding, toileting, grooming or other age-appropriate daily activities.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'),
]


def home(request):
    signs = [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in SIGNS]
    return render(request, 'home.html', {
        'active_page': 'home',
        'signs': signs,
        'meta_title': 'OT Cloud Therapy Center | Pediatric Occupational Therapy & Speech Pathology, Gurugram',
        'meta_description': "Evidence-based pediatric therapy in Gurugram — Occupational Therapy, Speech "
                            "Pathology, and Early Intervention. Helping children grow with clarity and confidence.",
    })


ABOUT_CHIPS = ['Sensory Integration', 'Neurodevelopmental Therapy', 'Autism Spectrum',
               'ADHD Management', 'Parental Coaching']

ABOUT_WORKFLOW = [
    ('Assessment', 'Multi-lens evaluation of your child'),
    ('Discussion', 'Clinicians meet to compare findings'),
    ('Planning', 'Drafting integrated shared goals'),
    ('Individual Therapy', 'Targeted one-on-one sessions'),
    ('Parent Involvement', 'Home strategies & coaching'),
    ('Progress Review', 'Measuring success quarterly'),
    ('Modification', 'Evolving the plan with the child'),
]

ABOUT_EXPECT = [
    ('Professional Behavior', 'Punctuality and respect in every interaction.'),
    ('Honest Communication', 'Transparent updates on progress and challenges.'),
    ('Ethical Recommendations', 'Only recommending what is clinically necessary.'),
    ('Safe, Child-Friendly Spaces', 'Clean, secure rooms thoughtfully set up for children to explore and learn.'),
    ('Evidence-Based Practice', 'Therapies grounded in the latest clinical research.'),
    ('Cultural Sensitivity', 'Respecting diverse family backgrounds and beliefs.'),
    ('Continuous Education', 'Staff undergo regular training sessions.'),
    ('Collaborative Spirit', "Willingness to talk to your child's school."),
]


def about(request):
    return render(request, 'about.html', {
        'active_page': 'about',
        'chips': ABOUT_CHIPS,
        'workflow': ABOUT_WORKFLOW,
        'expect': ABOUT_EXPECT,
        'meta_title': 'Meet Our Team | About OT Cloud Child Development & Therapy Centre',
        'meta_description': 'Behind every therapy session is a multidisciplinary team of specialists working '
                            'together to help every child reach their potential. Meet the OT Cloud team.',
    })


OT_DOMAINS = [
    ('Playing', '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="11" x2="10" y2="11"/><line x1="8" y1="9" x2="8" y2="13"/><line x1="15" y1="12" x2="15.01" y2="12"/><line x1="18" y1="10" x2="18.01" y2="10"/><path d="M17.32 5H6.68a4 4 0 0 0-3.98 3.6l-1.2 12A2 2 0 0 0 3.5 23a2 2 0 0 0 1.7-.94L7 19h10l1.8 3.06A2 2 0 0 0 20.5 23a2 2 0 0 0 2-2.4l-1.2-12A4 4 0 0 0 17.32 5z"/></svg>'),
    ('Learning', '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>'),
    ('Dressing', '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"/></svg>'),
    ('Feeding', '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v7c0 1.1.9 2 2 2h1v11h2V2M11 2v20h2V15c1.66 0 3-1.34 3-3V6c0-2.21-1.79-4-4-4"/></svg>'),
]

OT_BENEFITS = [
    ('Sensory Processing', 'Over-responsivity or under-responsivity to environmental stimuli.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7"/><path d="M2 12s3 7 10 7 10-7 10-7"/><circle cx="12" cy="12" r="2"/></svg>'),
    ('Fine Motor', 'Difficulty with handwriting, cutting, or manipulating small objects.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>'),
    ('Gross Motor', 'Coordination, balance, and core strength challenges.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="1"/><path d="M9 20l3-6 3 6"/><path d="M6 8l6 2 6-2"/><path d="M12 10v4"/></svg>'),
    ('Attention', 'Executive functioning and maintaining focus on tasks.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1"/></svg>'),
    ('Daily Living', 'Independence in dressing, grooming, and eating.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'),
    ('Emotional Regulation', 'Managing big feelings and transitioning between activities.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>'),
    ('School Skills', 'Sitting at a desk, following instructions, and organization.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>'),
    ('Play Skills', 'Imaginary play, taking turns, and social interaction.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>'),
]

OT_ASSESS = ['Fine Motor', 'Hand Function', 'Muscle Tone', 'Visual Perception', 'Core Stability',
             'Auditory Processing', 'Pre-Writing', 'Toileting Skills', 'Motor Planning', 'Proprioception',
             'Visual-Motor', 'Oral-Motor', 'Object Manipulation', 'Bilateral Integration', 'Sequencing',
             'Body Awareness', 'Alertness Level', 'Social Play']


SERVICES_INDEX = [
    ('Occupational Therapy', 'service_ot', 'Sensory processing, fine motor skills, and independence in daily life.',
     '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>', 'Explore Service →'),
    ('Speech & Language Therapy', 'service_speech', 'Communication, language development, and social interaction.',
     '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>', 'Explore Service →'),
    ('Early Intervention', 'service_early', 'Personalized support that harnesses the earliest years of brain development.',
     '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="10" r="5"/><path d="M9.5 9.5h.01M14.5 9.5h.01M9.5 12s1 1 2.5 1 2.5-1 2.5-1"/><path d="M5 21v-1a4 4 0 0 1 4-4h6a4 4 0 0 1 4 4v1"/></svg>', 'Explore Service →'),
    ('Special Education', 'service_se', 'Building the cognitive architecture for lifelong, confident learning.',
     '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>', 'Explore Service →'),
    ('Child Psychology', 'service_psychology', 'Emotional regulation and behavioural support — decoding the why behind behaviour.',
     '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 0 0-4 4 4 4 0 0 0-2 7 4 4 0 0 0 2 7 4 4 0 0 0 8 0 4 4 0 0 0 2-7 4 4 0 0 0-2-7 4 4 0 0 0-4-4z"/></svg>', 'Explore Service →'),
    ('Behavioural Modification', 'contact', 'Structured, positive strategies to reduce challenging behaviours and build helpful routines and self-regulation.',
     '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>', 'Enquire →'),
    ('Parent Counselling', 'contact', 'Guidance and emotional support for parents — practical strategies and a listening ear for the whole family.',
     '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>', 'Enquire →'),
]


def services(request):
    services_list = [{'title': t, 'url_name': u, 'desc': d, 'icon': i, 'link': l} for (t, u, d, i, l) in SERVICES_INDEX]
    return render(request, 'services_index.html', {
        'active_page': 'services',
        'services': services_list,
        'meta_title': 'Our Services | Pediatric Therapy Programmes | OT Cloud Gurugram',
        'meta_description': 'Explore OT Cloud\'s specialized pediatric services — Occupational Therapy, Speech & '
                            'Language Therapy, Early Intervention, Special Education, and Child Psychology.',
    })


def service_ot(request):
    domains = [{'label': l, 'icon': i} for (l, i) in OT_DOMAINS]
    benefits = [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in OT_BENEFITS]
    return render(request, 'services.html', {
        'active_page': 'service_ot',
        'domains': domains,
        'benefits': benefits,
        'assess': OT_ASSESS,
        'meta_title': 'Occupational Therapy for Children | OT Cloud Gurugram',
        'meta_description': 'Specialized pediatric occupational therapy focusing on sensory processing, fine motor '
                            'skills, and daily living independence — helping children participate confidently.',
    })


DEV_AREAS = [
    ('Communication', ['Expressing needs and desires', 'Understanding instructions', 'Using gestures and eye contact'],
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'),
    ('Social Interaction', ['Engaging in reciprocal play', 'Making and keeping friends', 'Understanding social cues'],
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>'),
    ('Sensory Processing', ['Response to noise or touch', 'Picky eating habits', 'Seeking constant movement'],
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7"/><path d="M2 12s3 7 10 7 10-7 10-7"/><circle cx="12" cy="12" r="2"/></svg>'),
    ('Attention & Regulation', ['Focus on tasks or play', 'Managing big emotions', 'Impulse control'],
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1"/></svg>'),
    ('Learning', ['Early literacy skills', 'Problem-solving abilities', 'Following school routines'],
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>'),
    ('Motor Development', ['Handwriting and fine motor', 'Balance and coordination', 'Strength and endurance'],
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6.5 6.5 17.5 17.5"/><path d="M21 21l-1-1"/><path d="M3 3l1 1"/><path d="M18 22l4-4"/><path d="M2 6l4-4"/><path d="M3 10l7-7"/><path d="M14 21l7-7"/></svg>'),
    ('Behaviour', ['Challenging transitions', 'Repetitive patterns', 'Flexibility in play'],
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>'),
    ('Daily Living Skills', ['Dressing and grooming', 'Sleep and toileting', 'Using utensils and drinking'],
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'),
]

CONDITIONS = ['Autism (ASD)', 'ADHD / ADD', 'Speech Delay', 'Dyspraxia (DCD)', 'Dyslexia',
              'Sensory Disorder', 'Global Delay', 'Down Syndrome', 'Cerebral Palsy', 'Anxiety / OCD']


def service_speech(request):
    return render(request, 'service_speech.html', {
        'active_page': 'service_speech',
        'meta_title': 'Speech & Language Therapy for Children | OT Cloud Gurugram',
        'meta_description': 'Specialized pediatric speech and language therapy — helping children communicate '
                            'with confidence, understanding, and connection through play-based intervention.',
    })


_EI_ICON = {
    'msg': '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    'move': '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="1"/><path d="M9 20l3-6 3 6"/><path d="M6 8l6 2 6-2"/><path d="M12 10v4"/></svg>',
    'play': '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>',
    'reg': '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.5 1-1a5.5 5.5 0 0 0 0-7.9z"/></svg>',
    'feed': '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v7c0 1.1.9 2 2 2h1v11h2V2M11 2v20h2V15c1.66 0 3-1.34 3-3V6c0-2.21-1.79-4-4-4"/></svg>',
    'social': '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    'cog': '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 0 0-4 4 4 4 0 0 0-2 7 4 4 0 0 0 2 7 4 4 0 0 0 8 0 4 4 0 0 0 2-7 4 4 0 0 0-2-7 4 4 0 0 0-4-4z"/></svg>',
    'sensory': '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
    'indep': '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    'bond': '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.42 4.58a5.4 5.4 0 0 0-7.65 0L12 5.35l-.77-.77a5.4 5.4 0 0 0-7.65 7.65l.77.77L12 20.66l7.65-7.66.77-.77a5.4 5.4 0 0 0 0-7.65z"/></svg>',
    'motor': '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="1"/><path d="M9 20l3-6 3 6"/><path d="M6 8l6 2 6-2"/></svg>',
    'flare': '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4M12 18v4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M2 12h4M18 12h4"/><circle cx="12" cy="12" r="3"/></svg>',
    'toys': '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>',
    'daily': '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"/></svg>',
}

EI_DOMAINS = [('Communication', 'msg'), ('Movement', 'move'), ('Play', 'play'), ('Self-Regulation', 'reg'),
              ('Feeding', 'feed'), ('Social Skills', 'social'), ('Cognitive Skills', 'cog'),
              ('Sensory Awareness', 'sensory'), ('Independence', 'indep'), ('Bonding', 'bond')]

EI_BENEFITS = [
    ('Communication', 'Support for delayed speech, limited gesturing, or difficulty expressing needs.', 'msg'),
    ('Motor Development', 'Assistance with crawling, walking, grasping objects, and coordination.', 'motor'),
    ('Social Interaction', 'Building eye contact, shared attention, and engagement with peers.', 'social'),
    ('Sensory Processing', 'Helping children manage reactions to lights, sounds, and textures.', 'flare'),
    ('Attention & Play', 'Fostering curiosity and the ability to focus on meaningful activities.', 'toys'),
    ('Daily Living Skills', 'Developing foundational routines for feeding, sleeping, and dressing.', 'daily'),
]

EI_CONDITIONS = ['Developmental Delay', 'ASD (Autism Spectrum)', 'Cerebral Palsy', 'Down Syndrome',
                 'Premature Birth Support', 'Genetic Conditions', 'Sensory Processing Disorder', 'Global Delay']

EI_ASSESS = ['Milestones', 'Eye Contact', 'Fine Motor', 'Gross Motor', 'Play Skills', 'Sensory Profile',
             'Attention', 'Feeding', 'Self-Care', 'Regulation', 'Posture', 'Social Cues', 'Muscle Tone',
             'Imitation', 'Communication']

EI_PROGRESS = ['Response to name', 'Increased curiosity', 'Better sleep patterns', 'New vocal sounds',
               'Improved hand control', 'Sharing toys', 'Following simple cues', 'Independent walking',
               'Reduced irritability', 'Willingness to explore']

EI_FAQ = [
    ('How do I know if my child needs early intervention?', 'If your child is not meeting developmental milestones for their age — in communication, movement, play, or social interaction — a screening can offer clarity. Trust your instinct; early is always safer than waiting.'),
    ('What age can a child start therapy?', 'We support children from infancy through the early years. The earlier support begins, the more we can leverage the brain\'s natural plasticity.'),
    ('Is play therapy just playing?', 'No. Every activity is a scientifically chosen clinical intervention designed to stimulate specific neural pathways and functional skills — it just feels like fun to the child.'),
    ('How often are the sessions?', 'Frequency is tailored to your child\'s needs and goals, agreed during the assessment feedback — typically ranging from weekly to several times a week.'),
    ('What is the role of the parent during sessions?', 'You are our greatest partner. We coach you in real time so the strategies continue at home, where most development happens.'),
    ('Do we need a doctor\'s referral?', 'No referral is required to begin. A formal diagnosis is not always necessary to start supporting your child\'s functional development.'),
    ('Is it too late to start if my child is 3?', 'It is never too late. While the earliest years offer the most plasticity, meaningful progress is achievable at every age.'),
    ('How are goals tracked and reported?', 'We set clear, measurable functional goals and review progress regularly, sharing transparent updates with you throughout the journey.'),
]


SE_BENEFITS = [
    ('School Readiness', 'Children transitioning to formal schooling who need a boost in foundational skills.'),
    ('Learning Difficulties', 'Struggles with reading, writing, or mathematics that fall behind peer averages.'),
    ('Attention & Executive Function', 'Children who find it hard to stay on task, organize thoughts, or manage time.'),
    ('Communication Gaps', 'Those who struggle to follow multi-step instructions or express complex thoughts.'),
    ('Cognitive Development', 'Children with delays in processing speed, abstract reasoning, or conceptual thinking.'),
    ('Adaptive Behaviour', 'Needs related to daily living, self-care, and functional independence in a classroom.'),
]

SE_CONDITIONS = ['Autism Spectrum Disorder (ASD)', 'ADHD / ADD', 'Dyslexia', 'Dysgraphia', 'Dyscalculia',
                 'Global Developmental Delay', 'Down Syndrome', 'Sensory Processing Disorder']

SE_ASSESS = ['Pre-academic', 'Literacy', 'Reading', 'Writing', 'Mathematics', 'Time Management', 'Spelling',
             'Phonics', 'Social Skills', 'Visual Processing', 'Auditory Skills', 'Self-Care', 'Reasoning',
             'Fine Motor', 'Working Memory', 'Following Instructions', 'Comprehension', 'Processing Speed']

SE_SR = ['Sitting Tolerance', 'Sustained Attention', 'Pencil Grip & Control', 'Pre-Writing Shapes',
         'Letter Recognition', 'Early Number Concepts', 'Following Routines', 'Sharing & Turn Taking',
         'Instructional Listening', 'Emotional Regulation']

SE_FAQ = [
    ('How is this different from tutoring?', 'Tutoring focuses on content (finishing a specific chapter), whereas Special Education focuses on the cognitive skills — processing, memory, attention — needed to understand any chapter.'),
    ('Do you work with the school teacher?', 'Yes. We provide detailed reports and can participate in IEP (Individualized Education Plan) meetings to ensure consistency across environments.'),
    ('How often should my child attend sessions?', 'Frequency is determined after the initial assessment, but most children benefit from 1–2 sessions per week.'),
]


PSY_CONDITIONS = ['Autism (ASD)', 'ADHD / ADD', 'Anxiety Disorders', 'ODD & CD',
                  'Sensory Processing Sensitivity', 'Learning Difficulties']

PSY_ASSESS = ['Executive Functioning', 'Anxiety Management', 'Impulse Control', 'Self-Esteem', 'Family Dynamics',
              'Academic Integration', 'Social Cognition', 'Cognitive Ability', 'Sleep Hygiene', 'Eating Behaviours',
              'Adaptive Functioning', 'Attachment Style', 'Processing Speed', 'Problem Solving', 'Sensory Integration']

PSY_PARTNER = ['Learning to respond calmly during a crisis.', 'Setting firm yet empathetic boundaries.',
               'Implementing positive reinforcement strategies.', 'Improving communication and bonding.']

PSY_PROGRESS = [
    ('Emotional Resilience', 'Noticeable reduction in the frequency and intensity of meltdowns or outbursts.'),
    ('Self-Advocacy', 'A child being able to use words to express "I need a break" or "I am feeling overwhelmed."'),
    ('Stronger Relationships', 'Better peer interactions and a more peaceful, cooperative home environment.'),
]

PSY_FAQ = [
    ('How do I know if my child needs psychological support?', 'If behavioral or emotional challenges are consistently impacting your child\'s ability to learn, socialize, or function at home, a professional assessment can provide clarity.'),
    ('Is this only for children with a diagnosis like ADHD?', 'No. Many children without a diagnosis benefit from support to manage anxiety, social changes, or big emotions during developmental transitions.'),
    ('How long does the assessment process take?', 'Typically the full 6-step process is completed over 4 to 6 weeks, allowing time for observations and comprehensive report writing.'),
    ('Do you work with the school?', 'Yes. With your permission, we can collaborate with teachers to ensure the strategies used in therapy are mirrored in the classroom.'),
    ('What is the difference between a tantrum and a meltdown?', 'Tantrums are often goal-oriented and can be managed with boundaries. Meltdowns are a sensory or emotional overload and require regulation and safety.'),
    ('Can I stay in the room during the sessions?', 'For younger children, parent involvement is often encouraged. For older children, we may recommend 1-on-1 time to build rapport.'),
    ('What if my child refuses to engage in therapy?', 'Our clinicians are experts in building rapport. We use play, technology, and the child\'s interests to meet them where they are.'),
    ('Will my child be labelled forever?', 'A diagnosis is a tool to unlock support and understanding. Our focus is on functional progress and happiness, not just labels.'),
    ('How often are the therapy sessions?', 'Most children attend weekly or fortnightly, depending on the clinical goals and family availability.'),
    ('What strategies can I use at home today?', 'Our blog offers immediate, evidence-based tips on emotional regulation you can start using right away.'),
]


def service_psychology(request):
    return render(request, 'service_psychology.html', {
        'active_page': 'service_psychology',
        'conditions': PSY_CONDITIONS,
        'assess': PSY_ASSESS,
        'partner': PSY_PARTNER,
        'progress': [{'title': t, 'desc': d} for (t, d) in PSY_PROGRESS],
        'faqs': PSY_FAQ,
        'meta_title': 'Child Psychology & Behavioural Support | OT Cloud Gurugram',
        'meta_description': 'Professional child psychology and behavioural support focused on emotional regulation '
                            'and understanding behaviour as communication. Compassionate, evidence-based care.',
    })


def service_se(request):
    return render(request, 'service_se.html', {
        'active_page': 'service_se',
        'benefits': [{'title': t, 'desc': d} for (t, d) in SE_BENEFITS],
        'conditions': SE_CONDITIONS,
        'assess': SE_ASSESS,
        'sr_checks': SE_SR,
        'faqs': SE_FAQ,
        'meta_title': 'Special Education Programme for Children | OT Cloud Gurugram',
        'meta_description': 'Special education that builds the cognitive architecture for lifelong learning — '
                            'multisensory, evidence-based strategies tailored to each child\'s neurological profile.',
    })


def service_early(request):
    return render(request, 'service_early.html', {
        'active_page': 'service_early',
        'domains': [{'label': l, 'icon': _EI_ICON[k]} for (l, k) in EI_DOMAINS],
        'benefits': [{'title': t, 'desc': d, 'icon': _EI_ICON[k]} for (t, d, k) in EI_BENEFITS],
        'conditions': EI_CONDITIONS,
        'assess': EI_ASSESS,
        'progress': EI_PROGRESS,
        'faqs': EI_FAQ,
        'meta_title': 'Early Intervention Programme for Children | OT Cloud Gurugram',
        'meta_description': 'Personalized early intervention that harnesses the critical window of early brain '
                            'development — helping infants and toddlers reach their full potential.',
    })


def concerns(request):
    areas = [{'title': t, 'points': p, 'icon': i} for (t, p, i) in DEV_AREAS]
    return render(request, 'concerns.html', {
        'active_page': 'concerns',
        'areas': areas,
        'conditions': CONDITIONS,
        'meta_title': 'Developmental Concerns Hub | Child Milestones & Support | OT Cloud',
        'meta_description': 'A guide for parents to understand child development milestones across ages and '
                            'recognise when professional support may help. Areas, conditions, and an age-wise guide.',
    })


def assessment(request):
    meta = {
        'active_page': 'assessment',
        'meta_title': 'Child Developmental Assessment | OT Cloud',
        'meta_description': 'A multidisciplinary clinical assessment that maps your child\'s developmental '
                            'profile and delivers a clear, actionable roadmap to progress.',
    }
    if request.method == 'POST':
        form = AssessmentRequestForm(request.POST)
        if form.is_valid():
            obj = form.save()
            _notify(
                f'New assessment request: {obj.child_name}',
                f'Parent: {obj.parent_name}\nEmail: {obj.email}\n'
                f'Concern: {obj.area_of_concern or "—"}\n\n{obj.message}',
                reply_to=obj.email,
            )
            return redirect(f"{reverse('assessment')}?submitted=1#booking")
    else:
        form = AssessmentRequestForm()

    return render(request, 'assessment.html', {
        **meta,
        'form': form,
        'submitted': request.GET.get('submitted') == '1',
    })


def resources(request):
    return render(request, 'resources.html', {
        'active_page': 'resources',
        'featured': BlogPost.objects.filter(status='published')[:3],
        'meta_title': 'Learning center | Child Development Resources | OT Cloud',
        'meta_description': 'Therapist-led resources, articles, and workshops to help parents understand child '
                            'development with confidence — evidence-based and jargon-free.',
    })


def blog_list(request):
    posts = BlogPost.objects.filter(status='published')
    return render(request, 'blog_list.html', {
        'active_page': 'blog',
        'posts': posts,
        'meta_title': 'Blog | Child Development Insights | OT Cloud',
        'meta_description': 'Insights, guidance, and clinical perspectives on child development, '
                            'occupational therapy, and speech pathology from the OT Cloud team.',
    })


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, status='published')
    recent = BlogPost.objects.filter(status='published').exclude(pk=post.pk)[:3]
    description = post.excerpt or Truncator(post.body).chars(160)
    image = post.cover_image.url if post.cover_image else None
    return render(request, 'blog_detail.html', {
        'active_page': 'blog',
        'post': post,
        'recent': recent,
        'meta_title': f'{post.title} | OT Cloud Blog',
        'meta_description': description,
        'meta_image': image,
        'og_type': 'article',
    })


def contact(request):
    meta = {
        'active_page': 'contact',
        'meta_title': 'Contact & Assessment Booking | OT Cloud Pediatric Therapy',
        'meta_description': 'Every journey begins with a conversation. Contact the OT Cloud team in Gurugram — '
                            'call, WhatsApp, or request an appointment for your child.',
    }
    if request.method == 'POST':
        form = AppointmentEnquiryForm(request.POST)
        if form.is_valid():
            obj = form.save()
            _notify(
                f'New appointment enquiry: {obj.child_name}',
                f'Parent: {obj.parent_name}\nChild: {obj.child_name} (age {obj.child_age or "—"})\n'
                f'Phone: {obj.phone}\nConcern: {obj.area_of_concern or "—"}\n'
                f'Prefers: {obj.get_contact_method_display() or "—"} · {obj.get_preferred_time_display() or "—"}\n\n'
                f'{obj.message}',
            )
            return redirect(f"{reverse('contact')}?submitted=1#booking-hub")
    else:
        form = AppointmentEnquiryForm()

    return render(request, 'contact.html', {
        **meta,
        'form': form,
        'submitted': request.GET.get('submitted') == '1',
    })


def milestone_check(request):
    return render(request, 'milestone_check.html', {
        'active_page': 'milestone',
        'meta_title': 'Free Milestone Checker | Is My Child on Track? | OT Cloud Gurugram',
        'meta_description': 'A quick, private 2-minute developmental milestone check for parents in Gurugram. '
                            'See if your child is meeting age-appropriate motor, speech, and social milestones.',
    })


def privacy(request):
    return render(request, 'privacy.html', {
        'active_page': 'privacy',
        'meta_title': 'Privacy Policy | OT Cloud Child Development & Therapy center',
        'meta_description': 'How OT Cloud collects, protects, and manages your family\'s personal and clinical '
                            'information, in line with India\'s Digital Personal Data Protection Act, 2023.',
    })


def terms(request):
    return render(request, 'terms.html', {
        'active_page': 'terms',
        'meta_title': 'Terms of Service | OT Cloud Child Development & Therapy center',
        'meta_description': 'The terms that govern the use of OT Cloud\'s website and services, our appointment '
                            'and cancellation approach, intellectual property, and cookie use.',
    })


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse('sitemap'))
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        '',
        f'Sitemap: {sitemap_url}',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')
