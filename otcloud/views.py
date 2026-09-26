from django.conf import settings
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db.models import F
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse


from .forms import (AppointmentEnquiryForm, AssessmentRequestForm, ContactForm,
                    MilestoneEnquiryForm)
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


# Distinct, condition-specific icons so parents recognise their concern at a glance.
def _icon(body, sw='2'):
    return ('<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{body}</svg>')


# Conditions listed directly on the home page.
HOME_CONDITIONS = [
    # Neurodiversity infinity loop
    ('Autism (ASD)', 'Support for social communication, interaction, play and repetitive behaviour patterns.',
     _icon('<path d="M12 12c1.8-2.1 3.5-4.3 6-4.3a4.3 4.3 0 1 1 0 8.6c-2.5 0-4.2-2.2-6-4.3-1.8-2.1-3.5-4.3-6-4.3a4.3 4.3 0 1 0 0 8.6c2.5 0 4.2-2.2 6-4.3z"/>')),
    # Restless energy: a bolt inside the head
    ('ADHD', 'Support for attention, impulse control, hyperactivity and everyday self-regulation.',
     _icon('<circle cx="12" cy="12" r="9.2"/><path d="M13.7 5.6 8.6 13.1h3.6l-1.9 5.5 5.1-7.5h-3.6z"/>')),
    # Heart with a sparkle: care and individuality
    ('Down Syndrome', 'Developmental support for speech, motor skills, learning and daily independence.',
     _icon('<path d="M12 20.6S3.9 15.4 3.9 10.1a4.1 4.1 0 0 1 8.1-1.1 4.1 4.1 0 0 1 8.1 1.1c0 5.3-8.1 10.5-8.1 10.5z"/><path d="m19.2 1.8.9 2.2 2.2.9-2.2.9-.9 2.2-.9-2.2-2.2-.9 2.2-.9z"/>')),
    # Walking figure with a support cane
    ('Cerebral Palsy', 'Therapy for posture, movement, coordination, hand function and mobility.',
     _icon('<circle cx="9.6" cy="4.3" r="1.9"/><path d="M9.6 8.1v4.4l-2.7 3.2L5.4 21"/><path d="M9.6 12.5l2.9 2.3.7 6.2"/><path d="M10.1 9.4l3.3 1.5 2.6-.9"/><path d="M18.6 6.4V21"/>')),
    # Emotional storms
    ('Behavioural and Emotional Disorders', 'Help with meltdowns, anxiety, rigid routines and emotional regulation.',
     _icon('<path d="M19 16.9A5 5 0 0 0 18 7h-1.26a8 8 0 1 0-11.62 9"/><polyline points="13 11 9.4 16.4 14.6 16.4 11 22"/>')),
    # Open book: reading and learning
    ('Learning Disabilities', 'Support for reading, writing, numeracy, attention and classroom participation.',
     _icon('<path d="M2.4 4.6h5.8A3.4 3.4 0 0 1 12 7.7v12a2.8 2.8 0 0 0-2.8-2.6H2.4z"/><path d="M21.6 4.6h-5.8A3.4 3.4 0 0 0 12 7.7v12a2.8 2.8 0 0 1 2.8-2.6h6.8z"/>')),
    # Speech bubble mid-conversation
    ('Speech and Language Disorders', 'Therapy for delayed speech, unclear speech, understanding and expression.',
     _icon('<path d="M21.2 11.4a8.6 8.6 0 0 1-9.2 8.6 9.3 9.3 0 0 1-3.9-.9L2.8 21.2l1.9-5.3a8.6 8.6 0 0 1-.9-4.5A8.6 8.6 0 0 1 12.4 2.8h.5a8.6 8.6 0 0 1 8.3 8.6z"/><path d="M8.6 11.4h.01M12.4 11.4h.01M16.2 11.4h.01" stroke-width="2.8"/>')),
    # Sensory input radiating in
    ('Sensory Processing Disorder', 'Support for strong or unusual responses to sound, touch, movement and textures.',
     _icon('<circle cx="12" cy="12" r="2.4"/><path d="M7.6 7.6a6.2 6.2 0 0 0 0 8.8"/><path d="M4.7 4.7a10.3 10.3 0 0 0 0 14.6"/><path d="M16.4 7.6a6.2 6.2 0 0 1 0 8.8"/><path d="M19.3 4.7a10.3 10.3 0 0 1 0 14.6"/>')),
]

# Google reviews shown on the home page. `photo` is an optional static path
# (e.g. 'assets/review-siddharth.webp'); when it is empty the coloured initial is used.
HOME_REVIEWS = [
    {'name': 'Siddharth Nobell', 'initial': 'S', 'colour': '#00685e', 'when': 'a month ago', 'photo': '',
     'text': "We want to express our deepest gratitude to the team at OT Cloud Therapy Center. Our daughter "
             "attended occupational therapy here for two to three years, and the journey has been truly "
             "transformative. The sessions were well structured, and we have seen meaningful, lasting changes "
             "in her behaviour, focus and independence. If you are looking for a supportive and effective "
             "pediatric therapy team, this center is highly recommended."},
    {'name': 'Shruti Bhargava', 'initial': 'S', 'colour': '#1e3a8a', 'when': '2 months ago', 'photo': '',
     'text': "We joined OT Cloud Therapy two years ago, when my daughter had a speech delay and was not able to "
             "speak fluently. Today she speaks and communicates with everyone easily. We are very happy with her "
             "progress and have seen a clear improvement in her speech clarity. Thank you to all the therapists "
             "and staff for their support and encouragement through their creative sessions and hard work."},
    {'name': 'Priyanka Agrawal', 'initial': 'P', 'colour': '#0b6fb8', 'when': '11 months ago', 'photo': '',
     'text': "We have had a wonderful experience at OT Cloud Therapy Centre. The team is extremely professional, "
             "caring and patient with our four-year-old son, and we have seen noticeable improvement in his speech "
             "and motor skills. They share regular updates and guide us as parents too. Highly recommended for "
             "anyone seeking quality occupational and speech therapy."},
    {'name': 'Priyanka Sharma', 'initial': 'P', 'colour': '#00873b', 'when': 'a year ago', 'photo': '',
     'text': "I am so grateful for the progress my daughter has made since she started occupational therapy at "
             "OT Cloud. Her physical abilities have improved, from climbing and jumping to her overall motor "
             "skills, and her interest in handwriting has grown remarkably — she is now excited to write and "
             "colour every day. The therapists are incredibly supportive and create a positive, encouraging "
             "environment for children to thrive."},
    {'name': 'Purnima Upadhyay', 'initial': 'P', 'colour': '#7c3aed', 'when': 'a year ago', 'photo': '',
     'text': "We are so grateful for the incredible team at OT Cloud. My child has made remarkable progress in "
             "both speech and occupational therapy, thanks to the dedication and expertise of Dheeraj Sir, Vashu "
             "Ma'am and Radhika Ma'am. Their personalised approach and constant encouragement have boosted my "
             "child's confidence, communication skills and motor abilities. We could not be happier with the care "
             "and support we have received."},
    {'name': 'Preeti Iyer', 'initial': 'P', 'colour': '#b45309', 'when': '3 years ago', 'photo': '',
     'text': "OT Cloud Therapy Centre is extremely good at understanding specially-abled children, helping them "
             "work on their weaknesses and build on their strengths. The therapists take special care to "
             "understand the parents' concerns and give personal attention to each child in every way possible. "
             "Thankful to Dr. Dheeraj Sir and the team for supporting us as parents and making a significant "
             "difference in our child's life."},
    {'name': 'Tinku Kumawat', 'initial': 'T', 'colour': '#be123c', 'when': '3 years ago', 'photo': '',
     'text': "Very satisfied with the occupational therapy at OT Cloud Therapy Center, especially with "
             "Dr. Dheeraj Suthar. He builds a genuine emotional connection with the child, which helps in getting "
             "results quickly. Thank you so much, Sir, for all your efforts."},
    {'name': 'Tanu Bansal', 'initial': 'T', 'colour': '#c2410c', 'when': 'a year ago', 'photo': '',
     'text': "A definite yes to the OT Cloud team — they are highly professional and provide excellent care. "
             "Before coming here, my son could speak only two-letter words; the speech and occupational therapy "
             "they provide really works. They build a special bond with the child, which helps so much with "
             "children who have special needs. Dheeraj Sir is like a pillar, and Ajay Sir, Khushboo Ma'am, "
             "Radhika Ma'am and Vasu Ma'am are all a wonderful team. Thank you for making our child blossom."},
]


def home(request):
    meta = {
        'active_page': 'home',
        'conditions': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in HOME_CONDITIONS],
        'reviews': HOME_REVIEWS,
        'meta_title': 'OT Cloud Therapy Center | Pediatric Occupational Therapy & Speech Pathology, Gurugram',
        'meta_description': "Evidence-based pediatric therapy in Gurugram — Occupational Therapy, Speech "
                            "Pathology, and Early Intervention. Helping children grow with clarity and confidence.",
    }
    # The home-page milestone check posts the parent's contact details back to this view.
    if request.method == 'POST':
        ms_form = MilestoneEnquiryForm(request.POST)
        if ms_form.is_valid():
            obj = ms_form.save()
            _notify(
                f'New milestone check enquiry: {obj.parent_name}',
                f'Parent: {obj.parent_name}\nPhone: {obj.phone or "—"}\nEmail: {obj.email or "—"}\n'
                f'Child age band: {obj.child_age or "—"}\n'
                f'Milestones ticked: {obj.milestones_done}/{obj.milestones_total} '
                f'({obj.not_yet} marked "not yet")',
                reply_to=obj.email or None,
            )
            return redirect(f"{reverse('home')}?ms=1#milestone-check")
    else:
        ms_form = MilestoneEnquiryForm()

    return render(request, 'home.html', {
        **meta,
        'ms_form': ms_form,
        'ms_submitted': request.GET.get('ms') == '1',
    })





# ---- About page (structure from the About OTCloud brief) ----
ABOUT_PILLARS = [
    ('Multidisciplinary Care', 'Specialists from different areas of child development working as one team.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>'),
    ('Individualised Goals', "Goals built around the child's own profile, pace and everyday needs.",
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1"/></svg>'),
    ('Parent Partnership', 'Families guided at every step, with strategies that work at home.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13.5 21v-1.8a4.2 4.2 0 0 0-4.2-4.2H6.2A4.2 4.2 0 0 0 2 19.2V21"/><circle cx="7.8" cy="7.2" r="3.9"/><path d="M21.3 5.6a2.2 2.2 0 0 0-3.1-.1l-.3.3-.3-.3a2.2 2.2 0 0 0-3.1 3.1l3.4 3.5 3.4-3.5a2.2 2.2 0 0 0 0-3z"/></svg>'),
]

ABOUT_MISSION_PILLARS = ['Empowering Teachers', 'Supporting Families', 'Promoting Early Identification',
                         'Strengthening Inclusive Education', 'Delivering Evidence-Based Practices',
                         'Building Sustainable School Partnerships']

ABOUT_VALUES = [
    ('Quality', 'Evidence-Based Practice',
     ['Clinical Excellence', 'Professional Standards', 'Measurable Results']),
    ('Transparency', 'Honest Communication',
     ['Ethical Decision-Making', 'Parent & School Collaboration', 'Clear Reporting']),
    ('Progress', 'Meaningful Outcomes',
     ['Functional Development', 'Continuous Improvement', 'Long-Term Impact']),
]

# One team, different areas of expertise. `photo` is filled as portraits are supplied.
ABOUT_TEAM = [
    ('Occupational Therapist', 'Sensory processing, motor skills, play and daily independence.', 'assets/rope-ladder.webp'),
    ('Speech & Language Therapist', 'Understanding, expression, speech clarity and social communication.', 'assets/oral-motor-therapy.webp'),
    ('Child Physiotherapist', 'Strength, balance, coordination, posture and mobility.', 'assets/ball-kick.webp'),
    ('Special Educator', 'Learning skills, academics and classroom participation.', 'assets/special-ed-3.webp'),
    ('Child Psychologist', 'Emotions, behaviour, attention and coping skills.', 'assets/therapist-child-hug.webp'),
    ('Therapy Assistants', 'Supporting sessions and carry-over under senior supervision.', 'assets/play-therapy-2.webp'),
]

ABOUT_PROCESS = [
    ('Assess', "Each discipline evaluates the child's profile in its own area.",
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg>'),
    ('Discuss', 'Findings are compared in a shared clinical discussion.',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15.5 13.5a2 2 0 0 1-2 2H7l-3.5 3V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2z"/><path d="M18.5 8.5h.5a2 2 0 0 1 2 2v9.5L18 17.5h-5"/></svg>'),
    ('Plan', 'One set of shared goals is agreed with the family.',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3.5h11l4 4V20a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 20V5a1.5 1.5 0 0 1 1-1.5z"/><path d="M8.5 12.5l2.2 2.2 4.3-4.3"/></svg>'),
    ('Support', 'Therapy runs alongside practical guidance for home and school.',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20.4S4.4 15.2 4.4 10.2A3.9 3.9 0 0 1 12 9a3.9 3.9 0 0 1 7.6 1.2c0 5-7.6 10.2-7.6 10.2z"/></svg>'),
    ('Review', 'Progress is measured at set points and goals are updated.',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 20.5h18"/><path d="M4 16.5l5-5 3.5 3L20 6"/><polyline points="15.5 6 20 6 20 10.5"/></svg>'),
]

ABOUT_SPACES = [
    ('Sensory Gym', 'assets/center-sensory-gym.webp', 'tall'),
    ('Assessment & Learning Room', 'assets/center-assessment-room.webp', ''),
    ('Parent Lounge', 'assets/center-parent-lounge.webp', ''),
    ('Reception', 'assets/center-reception.webp', 'tall'),
    ('Consultation Room', 'assets/center-consultation.webp', ''),
]

ABOUT_FAQS = [
    ('How are therapists assigned to my child?',
     "Following the initial assessment, our clinical lead assigns therapists based on your child's specific "
     "profile and the therapist's area of special interest and expertise."),
    ('Will my child always see the same therapist?',
     'Consistency is key for therapeutic rapport. We aim for full consistency, though assistants may '
     'occasionally support sessions under senior supervision for intensive programs.'),
    ('How does the team share information about my child?',
     'We use a centralized secure digital system and hold regular multidisciplinary clinical rounds where '
     "every child's progress is discussed across departments."),
    ('How many sessions a week are recommended?',
     'Most children benefit from 1–3 sessions per week. The exact number is recommended after the initial '
     "assessment, based on your child's profile and goals."),
    ('How long will therapy continue?',
     "It varies with each child's needs and goals. Many families see meaningful change within a few months, "
     'and we review progress regularly so therapy continues only as long as it is genuinely helping.'),
]


def about(request):
    return render(request, 'about.html', {
        'active_page': 'about',
        'pillars': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in ABOUT_PILLARS],
        'mission_pillars': ABOUT_MISSION_PILLARS,
        'values': [{'title': t, 'tagline': tag, 'points': p} for (t, tag, p) in ABOUT_VALUES],
        'team': [{'role': r, 'desc': d, 'photo': ph} for (r, d, ph) in ABOUT_TEAM],
        'process': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in ABOUT_PROCESS],
        'spaces': [{'title': t, 'image': img, 'size': sz} for (t, img, sz) in ABOUT_SPACES],
        'faqs': [{'q': q, 'a': a} for (q, a) in ABOUT_FAQS],
        'meta_title': 'Meet Our Team | About OT Cloud Child Development & Therapy Center',
        'meta_description': 'Behind every therapy session is a multidisciplinary team of specialists working '
                            'together to understand your child, set meaningful goals and support progress in '
                            'everyday life.',
    })




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
    ('Child Physiotherapy', 'service_physio', 'Strength, balance, coordination and mobility — helping children move and take part with confidence.',
     '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13" cy="4" r="1.9"/><path d="M12 7.8 9.4 12l3 2.4.9 6.4"/><path d="M9.4 12 6 15l-.6 5.8"/><path d="M12.8 9.2l3.2 1.6 2.6-.8"/></svg>', 'Explore Service →'),
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


# ---- Occupational Therapy page (structure from the OT services brief) ----
OT_HERO_TAGS = ['Fine Motor', 'Hand Function', 'Sensory Processing', 'Visual-Motor',
                'Handwriting', 'Motor Planning', 'Core Stability', 'Self-Care']

# The four things therapy is ultimately for.
OT_PILLARS = [
    ('Play', 'Building skills through purposeful play.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>'),
    ('Learn', 'Supporting classroom and learning participation.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.4 4.6h5.8A3.4 3.4 0 0 1 12 7.7v12a2.8 2.8 0 0 0-2.8-2.6H2.4z"/><path d="M21.6 4.6h-5.8A3.4 3.4 0 0 0 12 7.7v12a2.8 2.8 0 0 1 2.8-2.6h6.8z"/></svg>'),
    ('Self-Care', 'Building independence in everyday routines.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"/></svg>'),
    ('Participate', 'Helping children take part at home, school and in the community.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>'),
]

# "Who can benefit" — the everyday difficulties parents actually search for.
OT_BENEFIT_CARDS = [
    ('Handwriting', 'Pencil grip, writing and drawing.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>'),
    ('Fine Motor', 'Hands, fingers and coordination.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11.5V5.2a1.6 1.6 0 0 1 3.2 0v5.1"/><path d="M12.2 10.3V4.4a1.6 1.6 0 0 1 3.2 0v6.2"/><path d="M15.4 10.9V6.6a1.6 1.6 0 0 1 3.2 0v7.6a6.4 6.4 0 0 1-6.4 6.4h-1a5.6 5.6 0 0 1-4.3-2l-3-3.6a1.7 1.7 0 0 1 2.5-2.2L9 15"/></svg>'),
    ('Sensory', 'Textures, sounds and movement.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2.4"/><path d="M7.6 7.6a6.2 6.2 0 0 0 0 8.8M4.7 4.7a10.3 10.3 0 0 0 0 14.6"/><path d="M16.4 7.6a6.2 6.2 0 0 1 0 8.8M19.3 4.7a10.3 10.3 0 0 1 0 14.6"/></svg>'),
    ('Attention', 'Focus and participation.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.6"/><circle cx="12" cy="12" r="1"/></svg>'),
    ('Self-Care', 'Dressing, feeding and grooming.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"/></svg>'),
    ('Coordination', 'Balance and body control.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="4.2" r="1.9"/><path d="M12 8v5l-3 8"/><path d="M12 13l3.2 8"/><path d="M6.5 9.5 12 8l5.5 1.5"/></svg>'),
    ('Play Skills', 'Functional and age-appropriate play.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7.5" height="7.5" rx="2"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="2"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="2"/><circle cx="6.75" cy="17.25" r="3.75"/></svg>'),
    ('School Readiness', 'Skills needed for classroom participation.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7.5h16v12a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 19.5z"/><path d="M9 7.5V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2.5"/><path d="M4 12.5h16"/></svg>'),
]

# Conditions occupational therapy commonly supports, one or two lines each.
OT_CONDITIONS = [
    ('Autism Spectrum Disorder', 'Sensory processing, self-regulation, play, motor and daily living skills.'),
    ('ADHD', 'Attention, regulation, coordination and participation.'),
    ('Developmental Delay', 'Supporting age-appropriate developmental and functional skills.'),
    ('Sensory Processing Difficulties', 'Helping children manage and participate in everyday sensory experiences.'),
    ('Cerebral Palsy', 'Supporting functional movement, coordination, hand use and independence.'),
    ('Learning Difficulties', 'Supporting the underlying skills needed for classroom participation and learning.'),
    ('Handwriting Difficulties', 'Addressing the skills that contribute to comfortable and functional writing.'),
    ('Fine Motor Difficulties', 'Building hand strength, dexterity and coordinated hand use.'),
]

# Gallery of therapy in action. `image` is a static path, or '' until a photo is supplied.
OT_GALLERY = [
    ('Fine Motor Skills', 'Threading, pegs and small-object handling.', 'assets/fine-motor.webp', 'tall'),
    ('Sensory Processing', 'Swings, suspended equipment and sensory play.', 'assets/suspended-rings.webp', ''),
    ('Handwriting & Pre-Writing', 'Pre-writing patterns, letter formation and pencil control.', 'assets/writing-3.webp', ''),
    ('Coordination & Motor Planning', 'Obstacle courses, climbing and balance activities.', 'assets/obstacle-course.webp', 'tall'),
    ('Everyday Independence', 'Feeding, drinking and self-care routines.', 'assets/feeding-activity.webp', ''),
    ('Learning Through Play', 'Purposeful play that builds skill and confidence.', 'assets/play-therapy-4.webp', ''),
]

# Questions parents actually search for — also emitted as FAQ structured data.
OT_FAQS = [
    ('What is occupational therapy for children?',
     'Pediatric occupational therapy helps children develop the skills needed for everyday activities such '
     'as playing, learning, writing, eating, dressing, grooming and participating in school and home routines.'),
    ('How do I know if my child needs occupational therapy?',
     'You may consider an OT assessment if your child has ongoing difficulty with handwriting, pencil grip, '
     'fine motor skills, coordination, sensory processing, attention, self-care, play or school participation.'),
    ('What does a pediatric occupational therapist do?',
     "A pediatric occupational therapist assesses the skills affecting a child's everyday participation and "
     'develops individualized activities to support areas such as fine motor skills, sensory processing, '
     'coordination, handwriting, self-care, attention and motor planning.'),
    ('Can occupational therapy help with handwriting?',
     'Yes. OT can address the skills that support handwriting, including pencil grasp, hand strength, fine '
     'motor control, visual-motor coordination, posture, pencil control and letter formation. Handwriting is '
     'a common area of pediatric OT support.'),
    ('Can occupational therapy help with pencil grip?',
     "Yes. A therapist can look at the child's hand strength, finger coordination, grasp pattern, posture and "
     'visual-motor skills and work on the underlying skills needed for functional pencil use.'),
    ('Can occupational therapy help children with sensory issues?',
     'Occupational therapy can assess how a child responds to sensory input such as touch, sound, movement, '
     'textures and visual information and may provide individualized strategies to support participation and '
     'regulation.'),
    ('Can OT help a child with autism?',
     'Yes. OT may support children with autism in areas such as sensory processing, self-regulation, fine '
     'motor skills, motor planning, play, self-care and participation in everyday routines.'),
    ('Can occupational therapy help children with ADHD?',
     'OT may support children with ADHD in areas such as attention, self-regulation, organization, motor '
     'skills, sensory needs and participation in everyday activities.'),
    ('Can occupational therapy help with fine motor skills?',
     'Yes. OT can work on hand strength, finger coordination, grasp, dexterity, bilateral hand use and other '
     'skills needed for activities such as writing, drawing, cutting and manipulating objects.'),
    ('Can OT help my child become more independent?',
     'Yes. Occupational therapy can work on everyday skills such as dressing, feeding, grooming, toileting, '
     'using utensils, managing school materials and following daily routines.'),
    ('What happens during an occupational therapy assessment?',
     'The therapist discusses your concerns, observes how your child performs relevant activities, assesses '
     'appropriate developmental and functional skills, identifies strengths and areas requiring support, and '
     'uses the findings to guide therapy goals.'),
    ('Is occupational therapy the same as physiotherapy?',
     'No. Occupational therapy focuses strongly on participation in everyday activities, including fine motor '
     'skills, sensory processing, self-care, handwriting and functional independence. Physiotherapy primarily '
     'focuses on movement, strength, balance, mobility and physical function. The two can complement each '
     'other when needed.'),
    ('Does my child need a diagnosis to receive occupational therapy?',
     'Not necessarily. OT can be considered when a child is experiencing functional or developmental '
     'difficulties, even when there is no formal diagnosis.'),
    ('How long does a child need occupational therapy?',
     "It varies from child to child. The duration and frequency depend on the child's individual needs, "
     'functional goals, progress and response to therapy.'),
    ('Can occupational therapy help with school readiness?',
     'Yes. OT can support skills such as sitting and participating in activities, fine motor control, pencil '
     'skills, visual-motor coordination, following routines, attention and independence in classroom tasks.'),
]


def service_ot(request):
    return render(request, 'services.html', {
        'active_page': 'service_ot',
        'hero_tags': OT_HERO_TAGS,
        'pillars': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in OT_PILLARS],
        'benefits': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in OT_BENEFIT_CARDS],
        'conditions': [{'title': t, 'desc': d} for (t, d) in OT_CONDITIONS],
        'gallery': [{'title': t, 'desc': d, 'image': img, 'size': size} for (t, d, img, size) in OT_GALLERY],
        'faqs': [{'q': q, 'a': a} for (q, a) in OT_FAQS],
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


# ---- Speech & Language Therapy page (structure from the speech services brief) ----
SLT_HERO_TAGS = ['Speech', 'Language', 'Communication', 'Understanding', 'Social Communication']
SLT_FLOAT_LABELS = ['Communication', 'Language', 'Play-Based Learning']

# The four parts of communication therapy looks at.
SLT_PILLARS = [
    ('Understanding', 'Following instructions and understanding words, questions and concepts.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 12a6 6 0 1 1 12 0c0 2-1 3-2.2 3.9-1 .8-1.4 1.5-1.6 2.6a2.4 2.4 0 0 1-4.6-.3"/><path d="M9.5 10.5a2.5 2.5 0 0 1 4.4 1.6c0 1.1-.8 1.7-1.6 2.2"/><path d="M4 6.5 2.4 5.4M4.4 12H2.6M4.6 17.4 3 18.4"/></svg>'),
    ('Expressing', 'Using sounds, words, sentences or other ways to communicate thoughts and needs.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a7.5 7.5 0 0 1-7.5 7.5H8.6L4 22.4v-4.8A7.5 7.5 0 0 1 11.5 4.5h2A7.5 7.5 0 0 1 21 12z"/></svg>'),
    ('Speaking Clearly', 'Improving speech sound production and intelligibility.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5v3M6.5 7.5v9M10 4.5v15M13.5 8v8M17 10v4M20.5 11.4v1.2"/></svg>'),
    ('Social Communication', 'Taking turns, starting interactions, responding and maintaining conversations.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15.5 13.5a2 2 0 0 1-2 2H7l-3.5 3V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2z"/><path d="M18.5 8.5h.5a2 2 0 0 1 2 2v9.5L18 17.5h-5"/></svg>'),
]

# What parents commonly notice, grouped the way the brief sets it out.
SLT_NOTICE = [
    ('Speech', ['Speech is difficult for others to understand',
                'Difficulty producing certain sounds'],
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5v3M6.5 7.5v9M10 4.5v15M13.5 8v8M17 10v4M20.5 11.4v1.2"/></svg>'),
    ('Language', ['Fewer words than expected for their age',
                  'Difficulty combining words into sentences',
                  'Difficulty expressing wants, needs or ideas'],
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a7.5 7.5 0 0 1-7.5 7.5H8.6L4 22.4v-4.8A7.5 7.5 0 0 1 11.5 4.5h2A7.5 7.5 0 0 1 21 12z"/><path d="M8.6 12h.01M12 12h.01M15.4 12h.01" stroke-width="2.6"/></svg>'),
    ('Understanding', ['Difficulty following instructions',
                       'Difficulty answering questions',
                       'Difficulty understanding age-appropriate conversations'],
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 12a6 6 0 1 1 12 0c0 2-1 3-2.2 3.9-1 .8-1.4 1.5-1.6 2.6a2.4 2.4 0 0 1-4.6-.3"/><path d="M9.5 10.5a2.5 2.5 0 0 1 4.4 1.6c0 1.1-.8 1.7-1.6 2.2"/></svg>'),
    ('Social Communication', ['Difficulty starting or maintaining conversations',
                              'Difficulty taking turns while communicating',
                              'Difficulty communicating with peers',
                              'Limited use of gestures or other communication methods'],
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>'),
]

# Conditions, each linking through to the matching entry on the Concerns page.
SLT_CONDITIONS = [
    ('Autism Spectrum Disorder', 'Supporting communication, language development and social interaction.', 'autism'),
    ('Developmental Language Delay', 'Supporting understanding and use of age-appropriate language.', 'speech-language'),
    ('Speech Sound Difficulties', 'Helping children develop clearer speech and sound production.', 'speech-language'),
    ('Childhood Apraxia of Speech', 'Supporting speech planning and production through individualized intervention.', 'speech-language'),
    ('Stammering / Fluency Difficulties', 'Supporting more comfortable and effective communication.', 'speech-language'),
    ('ADHD', 'Supporting language organization, communication and social participation where needed.', 'adhd'),
    ('Developmental Delay', 'Supporting communication skills as part of overall developmental progress.', 'developmental-delay'),
    ('Neurological Conditions', 'Supporting communication and language needs associated with neurological conditions.', 'cerebral-palsy'),
]

# Photo-led gallery. Slots follow the brief's mosaic; `image` is filled as photos arrive.
SLT_GALLERY = [
    ('Building Vocabulary', 'Picture-based communication', 'assets/picture-communication-2.webp', 'g-01'),
    ('Learning Through Play', 'Play-based interaction', 'assets/play-therapy-2.webp', 'g-02'),
    ('Understanding & Expressing Language', 'Listening, responding and taking part', 'assets/picture-communication.webp', 'g-03'),
    ('Clearer Speech', 'Oral-motor and speech sound work', 'assets/oral-motor-therapy.webp', 'g-04'),
    ('Social Communication', 'Turn-taking in a small group', 'assets/play-therapy-1.webp', 'g-05'),
    ('Functional Communication', 'Making a choice or request', 'assets/expressing-feelings.webp', 'g-06'),
]

SLT_FAQS = [
    ('What is speech and language therapy for children?',
     'Speech and language therapy helps children develop the skills needed to understand language, express '
     'themselves, speak clearly and take part in everyday interactions at home, at school and with other children.'),
    ('When should I consider speech therapy for my child?',
     'Consider an assessment when your child is not meeting communication milestones, is difficult for others '
     'to understand, becomes frustrated trying to communicate, uses fewer words than children of a similar age, '
     'or when a teacher or doctor has raised a concern. Earlier support is usually shorter and more play-based.'),
    ('What is the difference between speech and language?',
     'Speech is how sounds and words are produced — clarity, articulation and fluency. Language is what a child '
     'understands and how they put words together to share meaning. A child may have strong language but unclear '
     'speech, or clear speech with limited language.'),
    ("How do I know if my child's speech is delayed?",
     'Professionals look at the whole picture: how much your child understands, how they express themselves, how '
     'clearly they speak, whether they use gestures, and whether new skills keep appearing. Fewer than around 20 '
     'words by 18 months, no two-word phrases by around two years, or speech that unfamiliar adults cannot '
     'understand after age three are all reasons to seek guidance.'),
    ('My child understands everything but does not speak much. Can speech therapy help?',
     'Yes. Strong understanding alongside limited spoken language is a common profile. Therapy builds expressive '
     'language through play, modelling, gestures, choices and structured opportunities to communicate, while '
     'checking that understanding is as strong as it appears.'),
    ('Can speech therapy help a child with autism?',
     'Yes. For autistic children, therapy may address functional communication, understanding, expressive '
     'language, social communication and play, including supportive communication methods such as gestures, '
     'pictures or devices where these help.'),
    ('Can speech therapy help with pronunciation?',
     'Yes. A therapist assesses which sounds are affected and why, then works on producing those sounds, hearing '
     'the difference between them, and using them in words, sentences and everyday conversation.'),
    ('What is receptive language?',
     'Receptive language is what a child understands — following instructions, understanding questions, '
     'vocabulary, concepts and spoken information. It usually develops ahead of expressive language.'),
    ('What is expressive language?',
     'Expressive language is how a child shares meaning — using sounds, words, sentences, gestures or other '
     'communication methods to express needs, ideas and experiences.'),
    ('Can speech therapy help my child understand instructions?',
     'Yes. Therapy can build the underlying skills — attention and listening, vocabulary, concepts and processing '
     'longer instructions — and give parents and teachers practical strategies such as simplifying language, '
     'pausing and pairing words with gestures or visuals.'),
    ('Can speech therapy help with social communication?',
     'Yes. Support may include starting and maintaining interactions, taking turns, staying on topic, repairing '
     'misunderstandings, understanding non-verbal cues and adapting communication to different situations.'),
    ('What happens during a speech and language assessment?',
     'The therapist discusses your concerns and developmental history, observes your child in play and structured '
     'tasks, and assesses understanding, expression, speech clarity and social communication. Hearing is '
     'considered as part of the picture. You receive the findings in plain language with clear recommendations.'),
    ('How long does speech therapy take?',
     "It varies. Duration depends on your child's profile, the goals agreed with the family, how consistently "
     'strategies are used at home and how your child responds. Progress is reviewed at set intervals rather than '
     'assumed.'),
    ('Does my child need a diagnosis to receive speech therapy?',
     'No. Therapy can be considered whenever communication difficulties are affecting everyday participation, '
     'with or without a formal diagnosis.'),
    ('Can speech therapy help a child who is not talking?',
     'Yes. For children who are not yet talking, therapy focuses on the foundations of communication — attention, '
     'interaction, imitation, play, gestures and understanding — and establishes a functional way to communicate, '
     'which may include gestures, pictures or a device alongside spoken language.'),
]


def service_speech(request):
    return render(request, 'service_speech.html', {
        'active_page': 'service_speech',
        'hero_tags': SLT_HERO_TAGS,
        'float_labels': SLT_FLOAT_LABELS,
        'pillars': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in SLT_PILLARS],
        'notice': [{'title': t, 'points': p, 'icon': i} for (t, p, i) in SLT_NOTICE],
        'conditions': [{'title': t, 'desc': d, 'anchor': a} for (t, d, a) in SLT_CONDITIONS],
        'gallery': [{'title': t, 'desc': d, 'image': img, 'slot': slot} for (t, d, img, slot) in SLT_GALLERY],
        'faqs': [{'q': q, 'a': a} for (q, a) in SLT_FAQS],
        'meta_title': 'Speech & Language Therapy for Children | OT Cloud Gurugram',
        'meta_description': 'Individualized pediatric speech and language therapy in Gurugram — supporting '
                            'understanding, expression, speech clarity and social communication so children can '
                            'connect with confidence.',
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


# ---- Child Psychology page (structure from the child psychology brief) ----
PSY_HERO_TAGS = ['Emotions', 'Behaviour', 'Attention', 'Social Skills']

PSY_PILLARS = [
    ('Emotional Development', 'Recognising, expressing and managing emotions.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20.4S4.4 15.2 4.4 10.2A3.9 3.9 0 0 1 12 9a3.9 3.9 0 0 1 7.6 1.2c0 5-7.6 10.2-7.6 10.2z"/></svg>'),
    ('Behavioural Skills', 'Understanding behaviour and developing appropriate responses.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 20.5h18"/><path d="M4 16.5l5-5 3.5 3L20 6"/><polyline points="15.5 6 20 6 20 10.5"/></svg>'),
    ('Social Skills', 'Building interaction, communication and relationships with others.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>'),
    ('Coping Skills', 'Learning practical ways to manage frustration, change and challenging situations.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.6 4 5.8v6c0 5 3.4 8.6 8 9.6 4.6-1 8-4.6 8-9.6v-6z"/><polyline points="9 12 11.2 14.2 15.2 10.2"/></svg>'),
]

# What prompts parents to ask for a consultation.
PSY_SIGNS = [
    ('Frequent Emotional Outbursts', 'Strong emotional reactions that are difficult to manage.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 16.9A5 5 0 0 0 18 7h-1.26a8 8 0 1 0-11.62 9"/><polyline points="13 11 9.4 16.4 14.6 16.4 11 22"/></svg>'),
    ('Anxiety or Excessive Worry', 'Persistent worries, fears or difficulty adjusting to situations.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9.2"/><path d="M8.4 15.4s1.3-1.6 3.6-1.6 3.6 1.6 3.6 1.6"/><line x1="9" y1="9.4" x2="9.01" y2="9.4"/><line x1="15" y1="9.4" x2="15.01" y2="9.4"/></svg>'),
    ('Attention & Impulse Control', 'Difficulty maintaining attention or managing impulsive responses.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.6"/><circle cx="12" cy="12" r="1"/></svg>'),
    ('Social Difficulties', 'Challenges with friendships, interaction or understanding social situations.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="9" r="3.4"/><circle cx="16.4" cy="9" r="3.4"/><path d="M2.6 20a5.4 5.4 0 0 1 10.8 0M13.6 20a5.4 5.4 0 0 1 7.8-4.8"/></svg>'),
    ('Behavioural Concerns', 'Repeated behaviours that interfere with home or school routines.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5.5h16v13a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 18.5z"/><path d="M8 3v5M16 3v5M4 10.5h16"/><path d="M9.5 14.5l2 2 3.5-3.5"/></svg>'),
    ('Changes in Mood or Behaviour', "Noticeable changes in the child's usual emotional or behavioural pattern.",
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 14c2.6-5 5.2-5 7.8 0s5.6 5 7.2 0"/><path d="M3 19.5h18"/><path d="M6.5 4.5h11"/></svg>'),
    ('Sleep & Routine Difficulties', 'Trouble settling, sleeping or coping with changes to daily routine.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>'),
    ('Confidence & Self-Esteem', 'Reluctance to try new things, or frequent negative talk about themselves.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20.5s-7.2-4.3-7.2-9.6a4.1 4.1 0 0 1 7.2-2.7 4.1 4.1 0 0 1 7.2 2.7c0 5.3-7.2 9.6-7.2 9.6z"/></svg>'),
]

# Compact grid — labels only, per the brief.
PSY_CONCERN_CHIPS = [
    'Anxiety & Excessive Worry',
    'Emotional Regulation Difficulties',
    'Behavioural Concerns',
    'Attention & Impulse-Control Difficulties',
    'Social Interaction Difficulties',
    'School Adjustment Concerns',
    'Low Confidence or Self-Esteem',
    'Autism-related Behavioural & Social Concerns',
    'ADHD-related Behavioural & Attention Concerns',
]

PSY_PROCESS = [
    ('Understand', "We begin by understanding the child's concerns, developmental history and everyday experiences."),
    ('Assess', 'Relevant emotional, behavioural, social or cognitive areas are explored using appropriate assessment methods.'),
    ('Plan', "Based on the findings, support goals and strategies are identified according to the child's needs."),
    ('Support & Review', 'Intervention focuses on practical skill development, with progress reviewed over time.'),
]

PSY_METHODS = [
    ('Play-Based Activities', '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7.5" height="7.5" rx="2"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="2"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="2"/><circle cx="6.75" cy="17.25" r="3.75"/></svg>'),
    ('Creative Expression', '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a9 9 0 1 0 0 18c1 0 1.8-.8 1.8-1.8 0-.5-.2-.9-.5-1.2-.3-.3-.5-.7-.5-1.2 0-1 .8-1.8 1.8-1.8H16a5 5 0 0 0 5-5c0-3.9-4-7-9-7z"/><circle cx="7.5" cy="11" r="1.2"/><circle cx="11" cy="7.2" r="1.2"/><circle cx="15.5" cy="8.6" r="1.2"/></svg>'),
    ('Age-Appropriate Conversation', '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15.5 13.5a2 2 0 0 1-2 2H7l-3.5 3V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2z"/><path d="M18.5 8.5h.5a2 2 0 0 1 2 2v9.5L18 17.5h-5"/></svg>'),
    ('Stories & Visual Tools', '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.4 4.6h5.8A3.4 3.4 0 0 1 12 7.7v12a2.8 2.8 0 0 0-2.8-2.6H2.4z"/><path d="M21.6 4.6h-5.8A3.4 3.4 0 0 0 12 7.7v12a2.8 2.8 0 0 1 2.8-2.6h6.8z"/></svg>'),
    ('Practical Behaviour Strategies', '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.6"/><circle cx="12" cy="12" r="1"/></svg>'),
]

PSY_PARENT_GUIDANCE = [
    'Understanding behavioural triggers',
    'Responding to emotional situations',
    'Establishing predictable routines',
    'Encouraging positive behaviour',
    'Supporting communication and emotional expression',
    'Managing everyday challenges consistently',
]

PSY_GALLERY = [
    ('Child-Friendly Interaction', 'assets/therapist-child-hug.webp', 'tall'),
    ('Emotional Expression Activities', 'assets/expressing-feelings.webp', ''),
    ('Structured Tasks', 'assets/play-block-board.webp', ''),
    ('Parent Guidance', 'assets/parent-consultation.webp', 'tall'),
    ('Social Skills Activities', 'assets/play-therapy-2.webp', ''),
    ('One-to-One Support', 'assets/ball-pit-play.webp', ''),
]

PSY_FAQS = [
    ('What is Child Psychology?',
     "Child Psychology focuses on understanding children's emotional, behavioural, social and cognitive development."),
    ('When should I consult a child psychologist?',
     'You may consider a consultation when emotional, behavioural, attention, social or adjustment concerns are '
     "affecting your child's everyday life."),
    ('Does my child need a diagnosis before seeing a psychologist?',
     'No. Parents can seek professional guidance when they have concerns, even without a formal diagnosis.'),
    ('Can Child Psychology help with behaviour problems?',
     'Yes. Psychological support can help understand behavioural patterns and develop appropriate strategies for '
     'managing challenging situations.'),
    ('Can a child psychologist help with anxiety?',
     'Yes. Psychological support can help children understand worries and develop age-appropriate coping strategies.'),
    ('Can Child Psychology help children with ADHD or autism?',
     'Psychological support may address areas such as emotional regulation, behaviour, attention, social '
     "interaction and coping skills according to the child's individual needs."),
    ('Are parents involved in the process?',
     'Yes. Parent guidance can be an important part of supporting behavioural and emotional skills outside '
     'therapy sessions.'),
]


def service_psychology(request):
    return render(request, 'service_psychology.html', {
        'active_page': 'service_psychology',
        'hero_tags': PSY_HERO_TAGS,
        'pillars': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in PSY_PILLARS],
        'signs': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in PSY_SIGNS],
        'chips': PSY_CONCERN_CHIPS,
        'process': [{'title': t, 'desc': d} for (t, d) in PSY_PROCESS],
        'methods': [{'title': t, 'icon': i} for (t, i) in PSY_METHODS],
        'guidance': PSY_PARENT_GUIDANCE,
        'gallery': [{'title': t, 'image': img, 'size': size} for (t, img, size) in PSY_GALLERY],
        'faqs': [{'q': q, 'a': a} for (q, a) in PSY_FAQS],
        'meta_title': 'Child Psychology for Children | Emotions, Behaviour & Attention | OT Cloud',
        'meta_description': "Child psychology support in Gurugram — understanding your child's emotions, "
                            'behaviour, attention and social skills, with practical guidance for parents.',
    })


# ---- Child Physiotherapy page (structure from the physiotherapy brief) ----
PHY_HERO_TAGS = ['Strength', 'Balance', 'Coordination', 'Mobility', 'Motor Development']
PHY_FLOAT_LABELS = ['Strength', 'Balance', 'Movement']

PHY_PILLARS = [
    ('Strength', 'Building the strength needed for age-appropriate movement and activities.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6.5 9.5v5M17.5 9.5v5M3.5 11v2M20.5 11v2M6.5 12h11"/></svg>'),
    ('Balance', 'Improving stability and control while sitting, standing, walking and moving.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="4.2" r="1.9"/><path d="M12 7.6v6.2M12 13.8 9 21M12 13.8 15 21"/><path d="M5 10.5h14"/></svg>'),
    ('Coordination', 'Supporting smoother and more controlled movement.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17c3-6 6-6 9 0s6 6 9 0"/><circle cx="3" cy="17" r="1.6"/><circle cx="21" cy="17" r="1.6"/></svg>'),
    ('Mobility', 'Helping children improve functional movement and participation.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13" cy="4" r="1.9"/><path d="M12 7.8 9.4 12l3 2.4.9 6.4"/><path d="M9.4 12 6 15l-.6 5.8"/><path d="M12.8 9.2l3.2 1.6 2.6-.8"/></svg>'),
]

# Who can benefit — 2 x 2 cards, each with a few short observations.
PHY_NOTICE = [
    ('Movement & Motor Skills', ['Delayed rolling, sitting, crawling or walking',
                                 'Difficulty running, jumping or climbing',
                                 'Slower to learn new movement skills',
                                 'Avoids physically demanding play'],
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13" cy="4" r="1.9"/><path d="M12 7.8 9.4 12l3 2.4.9 6.4"/><path d="M9.4 12 6 15l-.6 5.8"/><path d="M12.8 9.2l3.2 1.6 2.6-.8"/></svg>'),
    ('Strength & Posture', ['Tires quickly during physical activity',
                            'Slouching or difficulty sitting upright',
                            'Reduced endurance at school or during play',
                            'Difficulty holding a position for long'],
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6.5 9.5v5M17.5 9.5v5M3.5 11v2M20.5 11v2M6.5 12h11"/></svg>'),
    ('Balance & Coordination', ['Frequent falls or bumping into things',
                                'Difficulty standing on one leg',
                                'Clumsy or uncoordinated movement',
                                'Difficulty with stairs or uneven surfaces'],
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="4.2" r="1.9"/><path d="M12 7.6v6.2M12 13.8 9 21M12 13.8 15 21"/><path d="M5 10.5h14"/></svg>'),
    ('Mobility & Participation', ['Difficulty keeping up with other children',
                                  'Reluctance to join sports or playground activities',
                                  'Needs more physical help than expected',
                                  'A walking pattern that looks different'],
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 20.5h18"/><path d="M7.5 20.5V13M12 20.5V8.5M16.5 20.5V15"/><circle cx="12" cy="4.6" r="1.8"/></svg>'),
]

# Conditions, linking to the matching entry on the Concerns page where one exists.
PHY_CONDITIONS = [
    ('Cerebral Palsy', 'Supporting strength, mobility, balance, posture and functional movement.', 'cerebral-palsy'),
    ('Developmental Delay', 'Supporting gross motor development and age-appropriate physical skills.', 'developmental-delay'),
    ('Down Syndrome', 'Supporting strength, postural control, balance and motor development.', 'down-syndrome'),
    ('Neurological Conditions', 'Supporting movement, mobility, coordination and functional participation.', 'cerebral-palsy'),
    ('Muscular Dystrophy', "Supporting functional mobility, positioning and participation while considering the child's individual physical needs.", ''),
    ('Developmental Coordination Difficulties', 'Supporting coordination, balance, motor planning and physical participation.', 'coordination-difficulties'),
    ('Gait & Walking Difficulties', 'Assessing and supporting functional walking patterns and mobility.', 'coordination-difficulties'),
    ('Torticollis & Early Motor Concerns', 'Supporting positioning, movement symmetry and early motor development when appropriate.', ''),
]

PHY_GOALS = [
    ('Move With Greater Ease', 'Supporting functional movement across everyday environments.'),
    ('Build Physical Strength', 'Developing the strength required for age-appropriate activities.'),
    ('Improve Balance & Stability', 'Helping children maintain control during movement and different positions.'),
    ('Develop Better Coordination', 'Supporting smoother and more purposeful movements.'),
    ('Increase Functional Independence', 'Helping children participate more independently in age-appropriate activities.'),
    ('Participate in Everyday Play', 'Supporting physical participation at home, school and in the community.'),
]

PHY_JOURNEY = [
    ('Assess', 'Understanding how your child moves today.',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg>'),
    ('Plan', 'Setting goals around everyday needs.',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3.5h11l4 4V20a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 20V5a1.5 1.5 0 0 1 1-1.5z"/><path d="M8.5 12.5l2.2 2.2 4.3-4.3"/></svg>'),
    ('Practice', 'Purposeful, play-based movement activities.',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8.5"/><path d="M12 3.5c2.6 2.4 2.6 14.6 0 17M3.7 12h16.6"/></svg>'),
    ('Participate', 'Using new skills at home and school.',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/></svg>'),
    ('Progress', 'Reviewing change and adjusting goals.',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 20.5h18"/><path d="M4 16.5l5-5 3.5 3L20 6"/><polyline points="15.5 6 20 6 20 10.5"/></svg>'),
]

PHY_GALLERY = [
    ('Building Strength', 'Climbing and resistance activity', 'assets/climbing-ladder.webp', 'g-01'),
    ('Balance & Stability', 'Balance work with ankle weights', 'assets/balance-beam-1.webp', 'g-02'),
    ('Functional Mobility', 'Supported movement and mobility practice', 'assets/balance-beam-2.webp', 'g-03'),
    ('Gross Motor Skills', 'Kicking, stepping and whole-body movement', 'assets/ball-kick.webp', 'g-04'),
    ('Coordination & Motor Planning', 'Crawling through an obstacle course', 'assets/obstacle-course.webp', 'g-05'),
    ('Supported Movement Practice', 'Postural and movement work with support', 'assets/self-care-2.webp', 'g-06'),
]

# Grouped exactly as the brief sets out.
PHY_FAQ_GROUPS = [
    ('Understanding Child Physiotherapy', [
        ('What is child physiotherapy?',
         'Child physiotherapy helps children develop physical skills such as strength, balance, coordination, '
         'mobility, posture and functional movement.'),
        ('When should I consider physiotherapy for my child?',
         'Consider a physiotherapy assessment when your child has difficulty with movement, balance, strength, '
         'walking, coordination, physical participation or age-appropriate gross motor skills.'),
        ('Can physiotherapy help with delayed motor development?',
         "Yes. A pediatric physiotherapist can assess the child's current motor abilities and identify appropriate "
         'goals to support physical development and functional participation.'),
    ]),
    ('Movement & Motor Concerns', [
        ('Can physiotherapy help a child with cerebral palsy?',
         'Yes. Physiotherapy may support mobility, strength, balance, posture, movement control and functional '
         "participation based on the child's individual needs."),
        ('Can physiotherapy help my child learn to walk?',
         'Physiotherapy may support the development of the strength, balance, coordination and movement skills '
         "needed for functional mobility. The approach depends on the child's developmental and physical profile."),
        ('Why does my child fall frequently?',
         'Frequent falls may have different causes, including balance, coordination, strength, motor planning or '
         "other physical factors. An assessment can help understand the child's individual movement pattern."),
        ('Can physiotherapy improve balance?',
         'Yes. Therapy may include activities designed to develop postural control, balance reactions, '
         'coordination and stability.'),
        ('Can physiotherapy help with walking difficulties?',
         'Yes. A physiotherapist can assess walking and functional mobility and develop individualized goals '
         'where appropriate.'),
    ]),
    ('Therapy & Assessment', [
        ('Does my child need a diagnosis to receive physiotherapy?',
         'Not necessarily. A child may benefit from physiotherapy when movement or physical difficulties are '
         'affecting everyday participation, even without a formal diagnosis.'),
        ('How long does child physiotherapy take?',
         "The duration and frequency depend on the child's needs, therapy goals, progress and response to "
         'intervention.'),
        ('What happens during a child physiotherapy assessment?',
         "The physiotherapist discusses your concerns, observes the child's movement and assesses relevant "
         'physical and functional skills. The findings help guide therapy goals and recommendations.'),
    ]),
]


def service_physio(request):
    return render(request, 'service_physio.html', {
        'active_page': 'service_physio',
        'hero_tags': PHY_HERO_TAGS,
        'float_labels': PHY_FLOAT_LABELS,
        'pillars': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in PHY_PILLARS],
        'notice': [{'title': t, 'points': p, 'icon': i} for (t, p, i) in PHY_NOTICE],
        'conditions': [{'title': t, 'desc': d, 'anchor': a} for (t, d, a) in PHY_CONDITIONS],
        'goals': [{'title': t, 'desc': d} for (t, d) in PHY_GOALS],
        'journey': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in PHY_JOURNEY],
        'gallery': [{'title': t, 'desc': d, 'image': img, 'slot': slot} for (t, d, img, slot) in PHY_GALLERY],
        'faq_groups': [{'title': t, 'items': [{'q': q, 'a': a} for (q, a) in items]} for (t, items) in PHY_FAQ_GROUPS],
        'meta_title': 'Child Physiotherapy | Strength, Balance & Movement | OT Cloud Gurugram',
        'meta_description': 'Pediatric physiotherapy in Gurugram — helping children build strength, balance, '
                            'coordination, mobility and confidence in everyday movement.',
    })


# ---- Special Education page (structure from the special education brief) ----
SE_HERO_TAGS = ['Learning', 'Academics', 'Attention', 'Classroom Skills']

SE_PILLARS = [
    ('Academic Learning', 'Reading, writing, spelling and foundational academic concepts.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.4 4.6h5.8A3.4 3.4 0 0 1 12 7.7v12a2.8 2.8 0 0 0-2.8-2.6H2.4z"/><path d="M21.6 4.6h-5.8A3.4 3.4 0 0 0 12 7.7v12a2.8 2.8 0 0 1 2.8-2.6h6.8z"/></svg>'),
    ('Learning Skills', 'Attention, memory, understanding concepts and problem-solving.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a9 9 0 1 0 0 18c1 0 1.8-.8 1.8-1.8 0-.5-.2-.9-.5-1.2-.3-.3-.5-.7-.5-1.2 0-1 .8-1.8 1.8-1.8H16a5 5 0 0 0 5-5c0-3.9-4-7-9-7z"/><circle cx="7.6" cy="11" r="1.2"/><circle cx="11" cy="7.4" r="1.2"/><circle cx="15.4" cy="9" r="1.2"/></svg>'),
    ('Written Work', 'Letter formation, copying, written expression and completing worksheets.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>'),
    ('Classroom Readiness', 'Following routines, completing tasks and participating in classroom activities.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7.5h16v12a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 19.5z"/><path d="M9 7.5V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2.5"/><path d="M4 12.5h16"/></svg>'),
]

SE_SIGNS = [
    ('Reading & Writing', 'Difficulty developing age-appropriate literacy skills.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.4 4.6h5.8A3.4 3.4 0 0 1 12 7.7v12a2.8 2.8 0 0 0-2.8-2.6H2.4z"/><path d="M21.6 4.6h-5.8A3.4 3.4 0 0 0 12 7.7v12a2.8 2.8 0 0 1 2.8-2.6h6.8z"/></svg>'),
    ('Mathematics', 'Challenges with number concepts, calculations or understanding mathematical ideas.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="3.5" width="17" height="17" rx="3"/><path d="M7 8.5h4M9 6.5v4M13.4 8.5h3.6M13.4 14.2h3.6M13.4 17h3.6M7.4 13.6l2.8 2.8M10.2 13.6l-2.8 2.8"/></svg>'),
    ('Attention & Task Completion', 'Needs support to stay engaged and complete learning activities.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.6"/><circle cx="12" cy="12" r="1"/></svg>'),
    ('Understanding Concepts', 'Requires additional teaching, repetition or visual support to learn new concepts.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.2 17.5h5.6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5.9 1.1 1 1.8h5c.1-.7.4-1.3 1-1.8A6 6 0 0 0 12 3z"/></svg>'),
    ('Schoolwork', 'Needs individualized strategies to participate more effectively in academic tasks.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3.5h11l4 4V20a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 20V5a1.5 1.5 0 0 1 1-1.5z"/><path d="M8.5 12h7M8.5 16h4.5"/></svg>'),
    ('Learning Pace', 'Benefits from teaching that follows their own pace and learning style.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="13" r="8"/><path d="M12 9.5V13l2.4 1.6"/><path d="M9 2.5h6"/></svg>'),
    ('Memory & Recall', 'Difficulty remembering and applying what was taught in earlier lessons.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 20.5A4.5 4.5 0 0 1 5 16V9a4 4 0 0 1 4-4h.5a2.5 2.5 0 0 1 0 5"/><path d="M14.5 20.5A4.5 4.5 0 0 0 19 16V9a4 4 0 0 0-4-4h-.5a2.5 2.5 0 0 0 0 5"/><path d="M12 5v15.5"/></svg>'),
    ('Organisation & Study Skills', 'Support with planning work, managing materials and following routines.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4.5" width="18" height="16" rx="2"/><path d="M3 9.5h18"/><path d="M8 2.5v4M16 2.5v4"/><path d="M8 13.5h3M8 17h6"/></svg>'),
]

# Phrased as "may benefit" throughout — a condition never implies a need for support.
SE_BENEFIT_CHIPS = [
    'Learning Difficulties',
    'Specific Learning Disability (SLD)',
    'Dyslexia',
    'Dyscalculia',
    'ADHD',
    'Developmental Delays',
    'Autism Spectrum Disorder',
    'Intellectual & Developmental Disabilities',
    'Academic skill gaps',
]

SE_APPROACH = [
    ('Understand', "We identify the child's current academic and learning abilities.", 'Assessment',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg>'),
    ('Set Goals', "Learning goals are selected according to the child's needs and educational requirements.", 'Goal Setting',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1"/></svg>'),
    ('Teach & Practice', 'Concepts are taught using structured activities, visual supports and appropriate learning materials.', 'Teaching',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 9.5 12 5 2 9.5l10 4.5z"/><path d="M6 12v4.5c3 2.6 9 2.6 12 0V12"/></svg>'),
    ('Monitor Progress', 'Skills are reviewed regularly and learning goals are adjusted as the child progresses.', 'Progress Review',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 20.5h18"/><path d="M4 16.5l5-5 3.5 3L20 6"/><polyline points="15.5 6 20 6 20 10.5"/></svg>'),
]

SE_METHODS = [
    ('Visual Learning', 'Pictures, charts, visual schedules and demonstrations.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3.5" width="18" height="17" rx="2.5"/><circle cx="8.5" cy="9" r="1.6"/><path d="M21 16l-5-5L6.5 20.5"/></svg>'),
    ('Structured Teaching', 'Clear steps and predictable learning routines.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h4M4 12h4M4 18h4"/><path d="M12 6h8M12 12h8M12 18h8"/></svg>'),
    ('Hands-On Activities', 'Learning concepts through practical and interactive activities.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11.5V5.2a1.6 1.6 0 0 1 3.2 0v5.1"/><path d="M12.2 10.3V4.4a1.6 1.6 0 0 1 3.2 0v6.2"/><path d="M15.4 10.9V6.6a1.6 1.6 0 0 1 3.2 0v7.6a6.4 6.4 0 0 1-6.4 6.4h-1a5.6 5.6 0 0 1-4.3-2l-3-3.6a1.7 1.7 0 0 1 2.5-2.2L9 15"/></svg>'),
    ('Task Breakdown', 'Breaking complex tasks into smaller, manageable steps.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></svg>'),
    ('Repetition & Practice', 'Reinforcing concepts through repeated meaningful practice.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="21 4 21 10 15 10"/><polyline points="3 20 3 14 9 14"/><path d="M5.2 9A7.5 7.5 0 0 1 18 6.4L21 9M3 15l3 2.6A7.5 7.5 0 0 0 18.8 15"/></svg>'),
    ('Individualized Materials', "Worksheets and learning activities adapted to the child's level.",
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3.5h11l4 4V20a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 20V5a1.5 1.5 0 0 1 1-1.5z"/><path d="M8.5 12.5l2.2 2.2 4.3-4.3"/></svg>'),
]

SE_GALLERY = [
    ('Early Literacy Activities', 'Letters, numbers and early reading', 'assets/physical-activity.webp', 'g-01'),
    ('Reading Practice', 'Guided reading with the educator', 'assets/special-ed-1.webp', 'g-02'),
    ('Writing Skills', 'Letter formation and written work', 'assets/writing-2.webp', 'g-03'),
    ('Concept Learning', 'Working through written work together', 'assets/special-ed-3.webp', 'g-04'),
    ('Letter & Word Practice', 'Forming letters with supportive seating', 'assets/writing-1.webp', 'g-05'),
    ('Focus & Task Completion', 'Building attention through structured activity', 'assets/special-ed-4.webp', 'g-06'),
]

SE_FAQS = [
    ('What is Special Education?',
     'Special Education provides individualized teaching and learning support for children who need additional '
     'help with academic, learning or classroom skills.'),
    ('Does my child need a diagnosis for Special Education?',
     'Not necessarily. Educational support can be considered when a child is experiencing learning or academic '
     'difficulties, even when a formal diagnosis has not been made.'),
    ('Can Special Education help with reading and writing?',
     'Yes. Support may include foundational literacy, reading, spelling, writing and comprehension skills.'),
    ('Can Special Education help children with learning difficulties?',
     "Yes. Teaching strategies and learning goals can be adapted to the child's specific learning profile."),
    ('Is Special Education only for school-going children?',
     'No. Educational support can begin with foundational pre-academic skills and continue into school-age learning.'),
    ('How is Special Education different from tuition?',
     'Tuition generally focuses on subject teaching. Special Education focuses on how a child learns, adapting '
     'teaching methods, materials and goals to their individual needs.'),
    ('How are parents involved?',
     'Parents can receive practical suggestions for reinforcing learning skills and educational routines at home.'),
]


def service_se(request):
    return render(request, 'service_se.html', {
        'active_page': 'service_se',
        'hero_tags': SE_HERO_TAGS,
        'pillars': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in SE_PILLARS],
        'signs': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in SE_SIGNS],
        'chips': SE_BENEFIT_CHIPS,
        'approach': [{'title': t, 'desc': d, 'stage': st, 'icon': i} for (t, d, st, i) in SE_APPROACH],
        'methods': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in SE_METHODS],
        'gallery': [{'title': t, 'desc': d, 'image': img, 'slot': slot} for (t, d, img, slot) in SE_GALLERY],
        'faqs': [{'q': q, 'a': a} for (q, a) in SE_FAQS],
        'meta_title': 'Special Education for Children | Individualized Learning Support | OT Cloud',
        'meta_description': 'Special education in Gurugram — individualized teaching for reading, writing, '
                            'mathematics, attention and classroom skills, planned around how each child learns.',
    })


# ---- Early Intervention page (structure from the early intervention brief) ----
EI_HERO_TAGS = ['Communication', 'Movement', 'Learning', 'Play']

EI_PILLARS = [
    ('Communication', 'Understanding and expressing needs.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a7.5 7.5 0 0 1-7.5 7.5H8.6L4 22.4v-4.8A7.5 7.5 0 0 1 11.5 4.5h2A7.5 7.5 0 0 1 21 12z"/><path d="M8.6 12h.01M12 12h.01M15.4 12h.01" stroke-width="2.6"/></svg>'),
    ('Movement', 'Building coordination and motor skills.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13" cy="4" r="1.9"/><path d="M12 7.8 9.4 12l3 2.4.9 6.4"/><path d="M9.4 12 6 15l-.6 5.8"/><path d="M12.8 9.2l3.2 1.6 2.6-.8"/></svg>'),
    ('Learning', 'Developing attention and early learning abilities.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.4 4.6h5.8A3.4 3.4 0 0 1 12 7.7v12a2.8 2.8 0 0 0-2.8-2.6H2.4z"/><path d="M21.6 4.6h-5.8A3.4 3.4 0 0 0 12 7.7v12a2.8 2.8 0 0 1 2.8-2.6h6.8z"/></svg>'),
    ('Play & Interaction', 'Encouraging social connection and meaningful play.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>'),
]

# What parents notice first.
EI_SIGNS = [
    ('Speech & Communication', 'Few words, limited communication or difficulty understanding language.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15.5 13.5a2 2 0 0 1-2 2H7l-3.5 3V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2z"/><path d="M18.5 8.5h.5a2 2 0 0 1 2 2v9.5L18 17.5h-5"/></svg>'),
    ('Movement', 'Taking longer to develop sitting, crawling, standing or walking skills.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="4.2" r="1.9"/><path d="M12 7.6v6.2M12 13.8 9 21M12 13.8 15 21"/><path d="M5 10.5h14"/></svg>'),
    ('Play & Interaction', 'Difficulty engaging in play or interacting with others.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7.5" height="7.5" rx="2"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="2"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="2"/><circle cx="6.75" cy="17.25" r="3.75"/></svg>'),
    ('Learning & Attention', 'Difficulty staying engaged, imitating or learning new skills.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.6"/><circle cx="12" cy="12" r="1"/></svg>'),
    ('Daily Activities', 'Challenges with feeding, dressing or other age-appropriate routines.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"/></svg>'),
]

# Seven compact, scannable cards, each linking on to the Concerns page.
EI_CONDITION_CARDS = [
    ('Developmental Delay', 'When developmental skills are progressing at a slower pace.', 'developmental-delay'),
    ('Autism Spectrum Disorder', 'Supporting communication, interaction, play and learning.', 'autism'),
    ('Speech & Language Delay', 'Developing early communication and language abilities.', 'speech-language'),
    ('Cerebral Palsy', 'Working on movement, coordination and functional skills.', 'cerebral-palsy'),
    ('Motor Delay', 'Supporting gross and fine motor development.', 'coordination-difficulties'),
    ('Sensory Processing Difficulties', 'Helping children participate more comfortably in everyday activities.', 'sensory-processing'),
    ('Global Developmental Delay', 'Addressing developmental needs across multiple areas.', 'developmental-delay'),
]

EI_PROGRAM = [
    ('Understand', "We look at your child's current developmental abilities.",
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg>'),
    ('Plan', "Goals are selected according to the child's needs.",
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3.5h11l4 4V20a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 20V5a1.5 1.5 0 0 1 1-1.5z"/><path d="M8.5 12.5l2.2 2.2 4.3-4.3"/></svg>'),
    ('Learn & Practice', 'Skills are developed through engaging, meaningful activities.',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7.5" height="7.5" rx="2"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="2"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="2"/><circle cx="6.75" cy="17.25" r="3.75"/></svg>'),
    ('Review', 'Progress is monitored and goals are updated as the child develops.',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 20.5h18"/><path d="M4 16.5l5-5 3.5 3L20 6"/><polyline points="15.5 6 20 6 20 10.5"/></svg>'),
]

# One journey, several disciplines — each card links to that service page.
EI_TEAM = [
    ('Occupational Therapy', 'service_ot', '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11.5V5.2a1.6 1.6 0 0 1 3.2 0v5.1"/><path d="M12.2 10.3V4.4a1.6 1.6 0 0 1 3.2 0v6.2"/><path d="M15.4 10.9V6.6a1.6 1.6 0 0 1 3.2 0v7.6a6.4 6.4 0 0 1-6.4 6.4h-1a5.6 5.6 0 0 1-4.3-2l-3-3.6a1.7 1.7 0 0 1 2.5-2.2L9 15"/></svg>'),
    ('Speech & Language Therapy', 'service_speech', '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a7.5 7.5 0 0 1-7.5 7.5H8.6L4 22.4v-4.8A7.5 7.5 0 0 1 11.5 4.5h2A7.5 7.5 0 0 1 21 12z"/></svg>'),
    ('Child Physiotherapy', 'service_physio', '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13" cy="4" r="1.9"/><path d="M12 7.8 9.4 12l3 2.4.9 6.4"/><path d="M9.4 12 6 15l-.6 5.8"/><path d="M12.8 9.2l3.2 1.6 2.6-.8"/></svg>'),
    ('Special Education', 'service_se', '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.4 4.6h5.8A3.4 3.4 0 0 1 12 7.7v12a2.8 2.8 0 0 0-2.8-2.6H2.4z"/><path d="M21.6 4.6h-5.8A3.4 3.4 0 0 0 12 7.7v12a2.8 2.8 0 0 1 2.8-2.6h6.8z"/></svg>'),
    ('Behaviour Modification', 'service_psychology', '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 20.5h18"/><path d="M4 16.5l5-5 3.5 3L20 6"/><polyline points="15.5 6 20 6 20 10.5"/></svg>'),
    ('Sensory Integration Therapy', 'service_ot', '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2.4"/><path d="M7.6 7.6a6.2 6.2 0 0 0 0 8.8M4.7 4.7a10.3 10.3 0 0 0 0 14.6"/><path d="M16.4 7.6a6.2 6.2 0 0 1 0 8.8M19.3 4.7a10.3 10.3 0 0 1 0 14.6"/></svg>'),
]

EI_GALLERY_NEW = [
    ('Learning Through Play', 'Child playing with the therapist', 'assets/play-therapy-3.webp', 'g-01'),
    ('Building Communication', 'Listening and responding with the therapist', 'assets/picture-communication.webp', 'g-02'),
    ('Developing Hand Skills', 'Fine motor activity', 'assets/fine-motor.webp', 'g-03'),
    ('Growing Through Movement', 'Gross motor activity', 'assets/climbing-ladder.webp', 'g-04'),
    ('Exploring Sensory Experiences', 'Sensory and movement play', 'assets/suspended-rings.webp', 'g-05'),
    ('Early Learning Skills', 'Early learning activity', 'assets/early-learning.webp', 'g-06'),
]

EI_FAQS = [
    ('What is early intervention for children?',
     'Early intervention provides developmental support during the early years for children who may have delays '
     'or difficulties with communication, movement, learning, play or everyday skills.'),
    ('When should I consider early intervention?',
     'Consider it when your child has missed developmental milestones or you have concerns about speech, '
     'movement, learning, behaviour, play or social interaction.'),
    ('Does my child need a diagnosis?',
     'No. Early intervention can begin based on developmental concerns even without a formal diagnosis.'),
    ('Can early intervention help with speech delay?',
     'Yes. Speech and language therapy can be part of an early intervention program when communication '
     'development is a concern.'),
    ('Can early intervention help children with autism?',
     'Yes. It may address communication, social interaction, play, learning, sensory needs and daily skills.'),
    ('What areas does early intervention cover?',
     'It may include communication, motor development, cognitive skills, play, social interaction, sensory '
     'processing and self-care.'),
    ('How are parents involved?',
     'Parents can learn simple ways to encourage developmental skills during everyday routines at home.'),
]


def service_early(request):
    return render(request, 'service_early.html', {
        'active_page': 'service_early',
        'hero_tags': EI_HERO_TAGS,
        'pillars': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in EI_PILLARS],
        'signs': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in EI_SIGNS],
        'conditions': [{'title': t, 'desc': d, 'anchor': a} for (t, d, a) in EI_CONDITION_CARDS],
        'program': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in EI_PROGRAM],
        'team': [{'title': t, 'url': u, 'icon': i} for (t, u, i) in EI_TEAM],
        'gallery': [{'title': t, 'desc': d, 'image': img, 'slot': slot} for (t, d, img, slot) in EI_GALLERY_NEW],
        'faqs': [{'q': q, 'a': a} for (q, a) in EI_FAQS],
        'meta_title': 'Early Intervention for Children | Communication, Movement & Play | OT Cloud',
        'meta_description': 'Early intervention in Gurugram — timely developmental support for communication, '
                            'movement, learning, play and everyday skills in the early years.',
    })


# Conditions supported at OTCloud, as set out in the Concerns page brief.
# Each entry links on to the services that support it and to further reading.
def _svc(label, url):
    return {'label': label, 'url': url}

OT = _svc('Occupational Therapy', 'service_ot')
SLT = _svc('Speech & Language Therapy', 'service_speech')
SE = _svc('Special Education', 'service_se')
BEH = _svc('Behaviour Modification', 'service_psychology')
PHYSIO = _svc('Child Physiotherapy', 'service_physio')
SI = _svc('Sensory Integration Therapy', 'service_ot')

CONCERN_CONDITIONS = [
    {
        'title': 'Autism Spectrum Disorder (ASD)',
        'anchor': 'autism',
        'desc': 'Autism is a neurodevelopmental condition that can influence social communication, '
                'interaction, play, flexibility, behaviour and sensory processing. Every child is different, '
                'and strengths and support needs can vary considerably.',
        'notice_label': 'Parents may notice',
        'notice': ['Differences in social communication',
                   'Difficulty with back-and-forth interaction',
                   'Differences in play or flexibility',
                   'Repetitive movements or behaviours',
                   'Strong or unusual sensory responses',
                   'Difficulty adjusting to changes in routine'],
        'support': 'Support may focus on communication, social interaction, play, sensory regulation, '
                   'learning, behaviour and everyday independence.',
        'services': [OT, SLT, SE, BEH],
        'learn_label': 'Learn More About Autism',
        'topic': 'child-development',
    },
    {
        'title': 'Attention-Deficit / Hyperactivity Disorder (ADHD)',
        'anchor': 'adhd',
        'desc': 'ADHD can affect attention, activity level, impulse control and self-regulation. These '
                'differences may influence participation at home, school and in social situations.',
        'notice_label': 'Parents or teachers may notice',
        'notice': ['Difficulty sustaining attention',
                   'High activity levels',
                   'Impulsive responses',
                   'Difficulty following instructions',
                   'Challenges with routines and organisation',
                   'Difficulty regulating emotions'],
        'support': 'Intervention may focus on attention, self-regulation, classroom participation, '
                   'routines, behaviour and functional skills.',
        'services': [OT, BEH, SE],
        'learn_label': 'Learn More About ADHD',
        'topic': 'behaviour',
    },
    {
        'title': 'Speech & Language Concerns',
        'anchor': 'speech-language',
        'desc': 'Speech and language difficulties can affect how a child understands language, expresses '
                'ideas, communicates needs or produces speech clearly.',
        'notice_label': 'Parents may notice',
        'notice': ['Limited vocabulary',
                   'Delayed word combinations',
                   'Difficulty understanding instructions',
                   'Unclear speech',
                   'Difficulty expressing needs or ideas',
                   'Challenges with conversation'],
        'support': 'Speech and Language Therapy may address receptive language, expressive language, '
                   'speech development, social communication and functional communication.',
        'services': [SLT],
        'learn_label': 'Learn More About Speech & Language',
        'topic': 'speech-language',
    },
    {
        'title': 'Global Developmental Delay',
        'anchor': 'developmental-delay',
        'desc': 'Some children develop skills more slowly across one or more developmental areas. '
                "Understanding the child's overall developmental profile helps identify where support may "
                'be useful.',
        'notice_label': 'Areas that may be affected include',
        'notice': ['Communication', 'Motor development', 'Learning and cognition',
                   'Social interaction', 'Play', 'Self-care'],
        'support': 'Support may focus on early development, communication, motor skills, learning, play '
                   'and everyday independence.',
        'services': [OT, SLT, SE, PHYSIO],
        'learn_label': 'Learn More About Developmental Delay',
        'topic': 'child-development',
    },
    {
        'title': 'Cerebral Palsy',
        'anchor': 'cerebral-palsy',
        'desc': 'Cerebral Palsy primarily affects movement and posture and may also influence '
                'coordination, hand function, communication and participation.',
        'notice_label': 'Areas that may need support',
        'notice': ['Posture and positioning', 'Balance and coordination', 'Walking and mobility',
                   'Hand function', 'Fine motor skills', 'Self-care'],
        'support': 'Therapy can focus on functional movement, mobility, hand skills, positioning, '
                   'independence and participation in everyday activities.',
        'services': [OT, PHYSIO, SLT],
        'learn_label': 'Learn More About Cerebral Palsy',
        'topic': 'occupational-therapy',
    },
    {
        'title': 'Down Syndrome',
        'anchor': 'down-syndrome',
        'desc': 'Down Syndrome is a genetic condition associated with differences in physical development, '
                'communication, learning and overall development. Each child has individual strengths and '
                'support needs.',
        'notice_label': 'Areas that may need support',
        'notice': ['Communication and language', 'Motor development', 'Learning',
                   'Attention', 'Self-care', 'Social participation'],
        'support': 'Individualised therapy and educational support can help develop communication, motor, '
                   'learning and everyday functional skills.',
        'services': [OT, SLT, SE, PHYSIO],
        'learn_label': 'Learn More About Down Syndrome',
        'topic': 'child-development',
    },
    {
        'title': 'Developmental Coordination Difficulties',
        'anchor': 'coordination-difficulties',
        'desc': 'Some children experience ongoing difficulties with coordination and motor planning that '
                'can make everyday and school activities more challenging.',
        'notice_label': 'Parents or teachers may notice',
        'notice': ['Difficulty with handwriting', 'Difficulty using scissors or tools',
                   'Challenges with dressing', 'Difficulty learning new motor skills',
                   'Poor coordination during play or sports', 'Slower completion of motor-based tasks'],
        'support': 'Occupational Therapy may focus on motor coordination, motor planning, fine motor '
                   'skills, handwriting and functional independence.',
        'services': [OT],
        'learn_label': 'Learn More',
        'topic': 'occupational-therapy',
    },
    {
        'title': 'Learning Difficulties',
        'anchor': 'learning-difficulties',
        'desc': 'Learning difficulties can affect the development and use of academic skills. They may '
                'become more noticeable as school demands increase.',
        'notice_label': 'Areas that may be affected',
        'notice': ['Reading', 'Writing', 'Spelling', 'Mathematics',
                   'Attention during academic tasks', 'Following classroom instructions'],
        'support': 'Special Education and Occupational Therapy can support foundational learning, academic '
                   'skills, attention, classroom participation and functional learning strategies.',
        'services': [SE, OT],
        'learn_label': 'Learn More',
        'topic': 'learning',
    },
    {
        'title': 'Sensory Processing Concerns',
        'anchor': 'sensory-processing',
        'desc': 'Children may respond differently to sensory information such as sound, touch, movement, '
                'textures, lights or smells. These responses can affect regulation and everyday '
                'participation.',
        'notice_label': 'Parents may notice',
        'notice': ['Strong reactions to sounds', 'Avoidance of certain textures',
                   'Seeking movement or pressure', 'Difficulty in busy environments',
                   'Sensitivity during dressing or grooming', 'Difficulty staying regulated'],
        'support': 'Occupational Therapy may help children develop strategies for regulation and '
                   'participation in everyday activities.',
        'services': [OT, SI],
        'learn_label': 'Learn More',
        'topic': 'sensory-processing',
    },
    {
        'title': 'Emotional & Behavioural Concerns',
        'anchor': 'emotional-behavioural',
        'desc': 'Children may experience difficulties managing emotions, responding to expectations, '
                'following routines or adapting to changes.',
        'notice_label': 'Parents may notice',
        'notice': ['Frequent meltdowns', 'Difficulty with transitions', 'Strong emotional reactions',
                   'Difficulty following routines', 'Rigid patterns of behaviour',
                   'Challenges with self-regulation'],
        'support': 'Support may focus on understanding behaviour, building self-regulation, developing '
                   'positive responses and improving participation at home and school.',
        'services': [BEH, OT, SE],
        'learn_label': 'Learn More',
        'topic': 'behaviour',
    },
]

# Concerns that also warrant a paediatric medical opinion.
MEDICAL_FLAGS = ['Hearing', 'Vision', 'Feeding', 'Swallowing', 'Growth', 'Sleep', 'Pain', 'Seizures',
                 'Unusual Movements', 'Persistent Weakness', 'Loss of Previously Acquired Skills']


def concerns(request):
    areas = [{'title': t, 'points': p, 'icon': i} for (t, p, i) in DEV_AREAS]
    return render(request, 'concerns.html', {
        'active_page': 'concerns',
        'areas': areas,
        'conditions': CONCERN_CONDITIONS,
        'medical_flags': MEDICAL_FLAGS,
        'meta_title': 'Developmental Concerns Hub | Child Milestones & Support | OT Cloud',
        'meta_description': 'A guide for parents to understand child development milestones across ages and '
                            'recognise when professional support may help. Areas, conditions, and an age-wise guide.',
    })


# ---- Assessment page (structure from the assessment brief) ----
ASM_WHY = [
    ('Understand the Bigger Picture', 'Look at relevant developmental areas instead of focusing on one behaviour or skill.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1.6 12S5.6 4.8 12 4.8 22.4 12 22.4 12 18.4 19.2 12 19.2 1.6 12 1.6 12z"/><circle cx="12" cy="12" r="3"/></svg>'),
    ('Identify Priorities', 'Understand which areas are currently affecting communication, learning, participation or independence.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1"/></svg>'),
    ('Plan the Right Next Step', 'Use the findings to guide therapy, home strategies, school support, further assessment or referral when appropriate.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 20.5h18"/><path d="M4 16.5l5-5 3.5 3L20 6"/><polyline points="15.5 6 20 6 20 10.5"/></svg>'),
]

ASM_APPROACH = [
    ('Whole-Child View', 'We consider relevant areas such as communication, learning, movement, behaviour, sensory processing and daily skills.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4.5 21v-1.4A5.6 5.6 0 0 1 10 14h4a5.6 5.6 0 0 1 5.5 5.6V21"/></svg>'),
    ('Function-Focused', 'We look at how skills affect everyday activities at home, school and in the community.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'),
    ('Strength-Based', 'We identify existing abilities and emerging skills alongside areas that may need support.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.6l2.9 5.9 6.5.9-4.7 4.6 1.1 6.4L12 17.4l-5.8 3 1.1-6.4L2.6 9.4l6.5-.9z"/></svg>'),
    ('Family-Informed', 'Parent observations, developmental history and family priorities are an important part of the assessment.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>'),
]

ASM_EVALUATE = [
    ('Communication & Language', 'Speech, understanding, expression and functional communication.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a7.5 7.5 0 0 1-7.5 7.5H8.6L4 22.4v-4.8A7.5 7.5 0 0 1 11.5 4.5h2A7.5 7.5 0 0 1 21 12z"/><path d="M8.6 12h.01M12 12h.01M15.4 12h.01" stroke-width="2.6"/></svg>'),
    ('Attention, Thinking & Learning', 'Attention, problem-solving, cognitive and learning-related skills.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a9 9 0 1 0 0 18c1 0 1.8-.8 1.8-1.8 0-.5-.2-.9-.5-1.2-.3-.3-.5-.7-.5-1.2 0-1 .8-1.8 1.8-1.8H16a5 5 0 0 0 5-5c0-3.9-4-7-9-7z"/><circle cx="7.6" cy="11" r="1.2"/><circle cx="11" cy="7.4" r="1.2"/><circle cx="15.4" cy="9" r="1.2"/></svg>'),
    ('Motor & Coordination', 'Fine motor, gross motor, coordination and visual-motor abilities.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11.5V5.2a1.6 1.6 0 0 1 3.2 0v5.1"/><path d="M12.2 10.3V4.4a1.6 1.6 0 0 1 3.2 0v6.2"/><path d="M15.4 10.9V6.6a1.6 1.6 0 0 1 3.2 0v7.6a6.4 6.4 0 0 1-6.4 6.4h-1a5.6 5.6 0 0 1-4.3-2l-3-3.6a1.7 1.7 0 0 1 2.5-2.2L9 15"/></svg>'),
    ('Sensory & Regulation', 'Sensory processing, regulation and responses to everyday sensory experiences.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2.4"/><path d="M7.6 7.6a6.2 6.2 0 0 0 0 8.8M4.7 4.7a10.3 10.3 0 0 0 0 14.6"/><path d="M16.4 7.6a6.2 6.2 0 0 1 0 8.8M19.3 4.7a10.3 10.3 0 0 1 0 14.6"/></svg>'),
    ('Social, Behaviour & Emotional Skills', 'Social interaction, play, behaviour and emotional regulation.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="9" r="3.4"/><circle cx="16.4" cy="9" r="3.4"/><path d="M2.6 20a5.4 5.4 0 0 1 10.8 0M13.6 20a5.4 5.4 0 0 1 7.8-4.8"/></svg>'),
    ('Everyday Independence', 'Self-care, daily living, feeding/mealtime participation and functional skills.',
     '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"/></svg>'),
]

ASM_PREPARE = [
    ('Reports', 'Bring Relevant Reports', 'Previous therapy, medical, developmental or school reports, when available.',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3.5h11l4 4V20a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 20V5a1.5 1.5 0 0 1 1-1.5z"/><path d="M8.5 12h7M8.5 16h4.5"/></svg>'),
    ('Concerns', 'Share Your Concerns', 'Think about the skills or situations you would most like us to understand.',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15.5 13.5a2 2 0 0 1-2 2H7l-3.5 3V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2z"/><path d="M18.5 8.5h.5a2 2 0 0 1 2 2v9.5L18 17.5h-5"/></svg>'),
    ('Comfort', 'Comfort Matters', 'Children may need time to become familiar with a new environment and professional.',
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20.4S4.4 15.2 4.4 10.2A3.9 3.9 0 0 1 12 9a3.9 3.9 0 0 1 7.6 1.2c0 5-7.6 10.2-7.6 10.2z"/></svg>'),
    ('Parent Input', 'Parent Participation', "Your observations and information help us understand your child's everyday functioning.",
     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/></svg>'),
]

ASM_FAQS = [
    ('How long does a child assessment take?',
     "Assessment duration depends on the child's age, concerns, type of assessment and number of areas being "
     'evaluated. Some assessments may be completed in one session, while detailed assessments may require more '
     'time or multiple sessions.'),
    ('Can parents stay during the assessment?',
     "Parent involvement depends on the child's age, comfort and assessment requirements. Parents may be asked "
     'to remain present for part or all of the session.'),
    ('What if my child is shy or does not interact with the therapist?',
     'Children may need time to become comfortable. We may begin with familiar, play-based or low-demand '
     'activities and use observation to gather meaningful information.'),
    ('What if my child becomes overwhelmed during the assessment?',
     'The session can be adapted with breaks, changes in activity or a different approach depending on the '
     "child's needs."),
    ('What should I bring to the assessment?',
     'Bring relevant previous reports, school information, work samples or other documents that may help us '
     "understand your child's history and current needs."),
    ('Does an assessment mean my child will need therapy?',
     "Not necessarily. Recommendations are based on the assessment findings and your child's current needs. "
     'They may include guidance, monitoring, therapy, school strategies or further referral.'),
    ('When will we receive the findings?',
     'The timeline depends on the type and complexity of the assessment. The expected timeline will be '
     'explained by the team.'),
    ('How much does an assessment cost?',
     'Assessment fees vary according to the type and scope of assessment. Our team can explain the applicable '
     'fee before scheduling.'),
    ("Do I need a doctor's referral?",
     'No referral is needed. You can contact us directly to schedule an assessment for your child.'),
    ('Can both parents attend the session?',
     'Yes. We encourage both parents to join where possible — it gives us a fuller picture of your '
     "child's routines at home."),
    ('What age groups do you work with?',
     'We support children from early infancy up to 14 years of age.'),
    ('What types of therapy do you provide?',
     'Occupational Therapy, Speech and Language Therapy, Child Physiotherapy, Special Education, Child '
     'Psychology and behaviour support, along with sensory integration approaches within occupational therapy.'),
    ('How soon will we see progress?',
     "This varies with the child and the goals set. Many parents notice meaningful change within a few "
     'months of regular sessions, and progress is formally reviewed at agreed intervals.'),
    ('Can we get home strategies or activities to practise?',
     'Yes. Families are given practical home activities and strategies so progress continues between sessions.'),
]


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
                f'Parent: {obj.parent_name}\nPhone: {obj.phone or "—"}\nEmail: {obj.email}\n'
                f'Child: {obj.child_name} (age {obj.child_age or "—"})\n'
                f'Concern: {obj.area_of_concern or "—"}\n\n{obj.message}',
                reply_to=obj.email,
            )
            return redirect(f"{reverse('assessment')}?submitted=1#booking")
    else:
        form = AssessmentRequestForm()

    return render(request, 'assessment.html', {
        **meta,
        'form': form,
        'why': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in ASM_WHY],
        'approach': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in ASM_APPROACH],
        'evaluate': [{'title': t, 'desc': d, 'icon': i} for (t, d, i) in ASM_EVALUATE],
        'prepare': [{'title': t, 'desc': d, 'icon': i} for (st, t, d, i) in ASM_PREPARE],
        'faqs': [{'q': q, 'a': a} for (q, a) in ASM_FAQS],
        'submitted': request.GET.get('submitted') == '1',
    })


def resources(request):
    return render(request, 'resources.html', {
        'active_page': 'resources',
        'featured': BlogPost.objects.filter(status='published')[:3],
        'meta_title': 'Learning Center | Child Development Resources | OT Cloud',
        'meta_description': 'Therapist-led resources, articles, and workshops to help parents understand child '
                            'development with confidence — evidence-based and jargon-free.',
    })


# Topics parents browse the blog by. Keys match BlogPost.CATEGORY_CHOICES.
BLOG_TOPICS = [
    ('child-development', 'Child Development',
     'Milestones, developmental differences, early signs and everyday development.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 20.5h18"/><path d="M5 20.5V13M12 20.5V8.5M19 20.5V4.5"/></svg>'),
    ('occupational-therapy', 'Occupational Therapy',
     'Functional skills, fine motor development, independence, handwriting and participation.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11.5V5.2a1.6 1.6 0 0 1 3.2 0v5.1"/><path d="M12.2 10.3V4.4a1.6 1.6 0 0 1 3.2 0v6.2"/><path d="M15.4 10.9V6.6a1.6 1.6 0 0 1 3.2 0v7.6a6.4 6.4 0 0 1-6.4 6.4h-1a5.6 5.6 0 0 1-4.3-2l-3-3.6a1.7 1.7 0 0 1 2.5-2.2L9 15"/></svg>'),
    ('speech-language', 'Speech & Language',
     'Speech development, language, communication and social communication.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a7.5 7.5 0 0 1-7.5 7.5H8.6L4 22.4v-4.8A7.5 7.5 0 0 1 11.5 4.5h2A7.5 7.5 0 0 1 21 12z"/><path d="M8.6 12h.01M12 12h.01M15.4 12h.01" stroke-width="2.6"/></svg>'),
    ('sensory-processing', 'Sensory Processing',
     'Sensory responses, regulation, sensory strategies and everyday participation.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2.4"/><path d="M7.6 7.6a6.2 6.2 0 0 0 0 8.8M4.7 4.7a10.3 10.3 0 0 0 0 14.6"/><path d="M16.4 7.6a6.2 6.2 0 0 1 0 8.8M19.3 4.7a10.3 10.3 0 0 1 0 14.6"/></svg>'),
    ('behaviour', 'Behaviour & Emotional Regulation',
     'Understanding behaviour, transitions, routines, regulation and practical strategies.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 16.9A5 5 0 0 0 18 7h-1.26a8 8 0 1 0-11.62 9"/><polyline points="13 11 9.4 16.4 14.6 16.4 11 22"/></svg>'),
    ('learning', 'Learning & School Readiness',
     'Learning skills, handwriting, attention, classroom participation and school readiness.',
     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.4 4.6h5.8A3.4 3.4 0 0 1 12 7.7v12a2.8 2.8 0 0 0-2.8-2.6H2.4z"/><path d="M21.6 4.6h-5.8A3.4 3.4 0 0 0 12 7.7v12a2.8 2.8 0 0 1 2.8-2.6h6.8z"/></svg>'),
]

TOPIC_LABELS = {key: label for (key, label, _b, _i) in BLOG_TOPICS}

# One-line versions of the blurbs above, for the compact topic tiles on the blog hub.
TOPIC_TAGLINES = {
    'child-development': 'Milestones and early signs',
    'occupational-therapy': 'Motor skills and everyday independence',
    'speech-language': 'Talking, understanding and communication',
    'sensory-processing': 'Sensory responses and regulation',
    'behaviour': 'Routines, transitions and big feelings',
    'learning': 'Attention, handwriting and school skills',
}


def _published():
    return BlogPost.objects.filter(status='published')


def _top_up(posts, pool, count):
    """Pad a short row with further posts so a section never renders half-empty."""
    chosen = list(posts[:count])
    if len(chosen) < count:
        seen = {p.pk for p in chosen}
        for extra in pool:
            if extra.pk not in seen:
                chosen.append(extra)
                seen.add(extra.pk)
            if len(chosen) == count:
                break
    return chosen


BLOG_FEED_PER_PAGE = 4
BLOG_ALL_PER_PAGE = 12
PAGE_LINKS_PER_BLOCK = 6


def _paginate(request, posts, per_page):
    """Return the requested page plus the fixed block of page numbers around it:
    pages 1-6 while on 1-6, then 7-12 while on 7-12, and so on."""
    page = Paginator(posts, per_page).get_page(request.GET.get('page'))
    start = (page.number - 1) // PAGE_LINKS_PER_BLOCK * PAGE_LINKS_PER_BLOCK + 1
    end = min(start + PAGE_LINKS_PER_BLOCK - 1, page.paginator.num_pages)
    return page, range(start, end + 1)


def blog_list(request):
    """Two jobs, two sections: a way to browse by topic, and one paginated feed
    of everything published (articles and guides alike)."""
    published = _published()

    topics = [{'slug': key, 'title': label, 'desc': TOPIC_TAGLINES.get(key, blurb), 'icon': icon,
               'count': published.filter(category=key).count()}
              for (key, label, blurb, icon) in BLOG_TOPICS]

    feed, page_range = _paginate(request, published, BLOG_FEED_PER_PAGE)

    return render(request, 'blog_list.html', {
        'active_page': 'blog',
        'topics': topics,
        'feed': feed,
        'page_range': page_range,
        'meta_title': 'Blog | Practical Information for Understanding Your Child | OT Cloud',
        'meta_description': 'Clear, evidence-informed articles and parent guides on child development, '
                            'occupational therapy, speech and language, sensory processing, behaviour '
                            'and learning from the OT Cloud therapy team.',
    })


def blog_all(request):
    posts, page_range = _paginate(request, _published(), BLOG_ALL_PER_PAGE)
    return render(request, 'blog_all.html', {
        'active_page': 'blog',
        'posts': posts,
        'page_range': page_range,
        'topics': [{'slug': k, 'title': l} for (k, l, _b, _i) in BLOG_TOPICS],
        'meta_title': 'All Articles & Parent Guides | OT Cloud Blog',
        'meta_description': 'Every article and parent guide from the OT Cloud therapy team, newest first — '
                            'child development, therapy, speech, sensory processing, behaviour and learning.',
    })


def blog_topic(request, topic):
    # Parent Guides was folded into the topical categories; keep old links working.
    if topic == 'parent-guides':
        return redirect('blog_list', permanent=True)
    if topic not in TOPIC_LABELS:
        raise Http404('Unknown topic')
    label = TOPIC_LABELS[topic]
    blurb = next(b for (k, _l, b, _i) in BLOG_TOPICS if k == topic)
    posts = _published().filter(category=topic)
    return render(request, 'blog_topic.html', {
        'active_page': 'blog',
        'topic': topic,
        'topic_title': label,
        'topic_desc': blurb,
        'posts': posts,
        'topics': [{'slug': k, 'title': l} for (k, l, _b, _i) in BLOG_TOPICS],
        'meta_title': f'{label} Articles & Guides | OT Cloud Blog',
        'meta_description': blurb,
    })


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, status='published')
    # Read count drives the "Parents Are Reading" row on the blog hub.
    BlogPost.objects.filter(pk=post.pk).update(views=F('views') + 1)

    published = _published().exclude(pk=post.pk)
    related = _top_up(published.filter(category=post.category), published, 3)

    description = post.summary
    image = post.cover_image.url if post.cover_image else None
    return render(request, 'blog_detail.html', {
        'active_page': 'blog',
        'post': post,
        'related': related,
        'topic_title': TOPIC_LABELS.get(post.category, 'Blog'),
        'meta_title': post.meta_title or f'{post.title} | OT Cloud Blog',
        'meta_description': description,
        'word_count': len(post.plain_text.split()),
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
