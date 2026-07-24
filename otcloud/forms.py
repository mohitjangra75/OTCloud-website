from django import forms

from .models import AppointmentEnquiry, AssessmentRequest, ContactMessage


class AppointmentEnquiryForm(forms.ModelForm):
    class Meta:
        model = AppointmentEnquiry
        fields = ['parent_name', 'child_name', 'child_age', 'phone',
                  'area_of_concern', 'contact_method', 'preferred_time', 'message']


class AssessmentRequestForm(forms.ModelForm):
    class Meta:
        model = AssessmentRequest
        fields = ['child_name', 'child_dob', 'parent_name', 'email',
                  'area_of_concern', 'message']


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'message']
