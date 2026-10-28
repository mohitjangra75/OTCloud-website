import re

from django import forms

from .models import (AppointmentEnquiry, AssessmentRequest, ContactMessage,
                     MilestoneEnquiry)


def normalise_mobile(value):
    """Accept an Indian mobile number typed any common way (+91, 91 or 0 prefix, spaces,
    dashes, brackets) and return it as +919876543210, so admin search on the 10 digits works."""
    match = re.fullmatch(r'(?:\+91|91|0)?([6-9]\d{9})', re.sub(r'[\s\-().]', '', value))
    if not match:
        raise forms.ValidationError('Please enter a valid 10-digit mobile number.')
    return f'+91{match.group(1)}'


class AppointmentEnquiryForm(forms.ModelForm):
    class Meta:
        model = AppointmentEnquiry
        fields = ['parent_name', 'child_name', 'child_age', 'phone',
                  'area_of_concern', 'contact_method', 'preferred_time', 'message']

    def clean_phone(self):
        return normalise_mobile(self.cleaned_data['phone'])


class AssessmentRequestForm(forms.ModelForm):
    CONCERN_OPTIONS = [
        ('speech', 'Speech and communication'),
        ('social', 'Social interaction and play'),
        ('sensory', 'Sensory processing'),
        ('attention', 'Attention and regulation'),
        ('behaviour', 'Behaviour or emotional regulation'),
        ('academic', 'Learning or school participation'),
        ('motor', 'Movement and coordination'),
        ('feeding', 'Feeding or mealtime participation'),
        ('daily', 'Daily living skills'),
        ('other', 'Other'),
    ]
    area_of_concern = forms.ChoiceField(choices=CONCERN_OPTIONS, required=False)
    phone = forms.CharField(required=True)

    class Meta:
        model = AssessmentRequest
        fields = ['parent_name', 'phone', 'email', 'child_name', 'child_age',
                  'area_of_concern', 'message']

    def clean_phone(self):
        return normalise_mobile(self.cleaned_data['phone'])


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'message']


# Age bands offered by the home-page milestone check. The quiz posts the label as
# child_age, so the buttons are rendered from this list to keep the two in step.
MILESTONE_AGE_BANDS = [
    ('12m', 'By 12 months'),
    ('2y', 'By 2 years'),
    ('3y', 'By 3 years'),
    ('4y', 'By 4 years'),
    ('5y', 'By 5 years'),
    ('6y', '5+ years (school age)'),
]


class MilestoneEnquiryForm(forms.ModelForm):
    """Captures the parent's details after the milestone check. Either a phone
    number or an email address is required — not necessarily both."""

    class Meta:
        model = MilestoneEnquiry
        fields = ['parent_name', 'phone', 'email', 'child_age',
                  'milestones_done', 'milestones_total']
        widgets = {
            'child_age': forms.HiddenInput(),
            'milestones_done': forms.HiddenInput(),
            'milestones_total': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_name'].label = 'Your name'
        self.fields['phone'].label = 'Mobile number'
        self.fields['email'].label = 'Email address'
        for name in ('child_age', 'milestones_done', 'milestones_total'):
            self.fields[name].required = False

    def came_from_quiz(self):
        """The quiz script fills the hidden fields with a known age band and the ticked
        count. Bots posting the form directly leave them at 0/0 or stuff in random text."""
        total = self.cleaned_data.get('milestones_total') or 0
        done = self.cleaned_data.get('milestones_done') or 0
        return (self.cleaned_data.get('child_age') in {label for _, label in MILESTONE_AGE_BANDS}
                and 0 < total and done <= total)

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        return normalise_mobile(phone) if phone else phone

    def clean(self):
        cleaned = super().clean()
        # A number that was typed but rejected already has its own error explaining why.
        if not cleaned.get('phone') and not cleaned.get('email') and not self.has_error('phone'):
            raise forms.ValidationError(
                'Please share either a mobile number or an email address so our team can reach you.'
            )
        return cleaned
