from django import forms

class CSVUploadForm(forms.Form):
    file = forms.FileField(label="Upload CSV File")  # Ensure it's named 'file'
