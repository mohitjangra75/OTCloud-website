from django import forms

from .models import (AppointmentEnquiry, AssessmentRequest, ContactMessage,
                     MilestoneEnquiry)


class AppointmentEnquiryForm(forms.ModelForm):
    class Meta:
        model = AppointmentEnquiry
        fields = ['parent_name', 'child_name', 'child_age', 'phone',
                  'area_of_concern', 'contact_method', 'preferred_time', 'message']


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


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'message']


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

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('phone') and not cleaned.get('email'):
            raise forms.ValidationError(
                'Please share either a mobile number or an email address so our team can reach you.'
            )
        return cleaned
