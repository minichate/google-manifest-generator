from django import forms

class GoogleConfigurationForm(forms.Form):
    admin_email = forms.EmailField(required=True)
    consumer_key = forms.CharField(max_length=100, required=True)
    consumer_secret = forms.CharField(max_length=100, required=True)
