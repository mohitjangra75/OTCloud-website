from django import forms

from .models import AppointmentEnquiry, AssessmentRequest, ContactMessage


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
    phone = forms.CharField(required=False)

    class Meta:
        model = AssessmentRequest
        fields = ['child_name', 'child_dob', 'parent_name', 'phone', 'email',
                  'area_of_concern', 'message']


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'message']
