from django import forms
from datetime import datetime


class CSVUploadForm(forms.Form):
    file = forms.FileField(label="Upload CSV File")  # Ensure it's named 'file'

class IntakeSelectionForm(forms.Form):
    MONTH_CHOICES = [
        ("January", "January"), ("February", "February"), ("March", "March"),
        ("April", "April"), ("May", "May"), ("June", "June"),
        ("July", "July"), ("August", "August"), ("September", "September"),
        ("October", "October"), ("November", "November"), ("December", "December"),
    ]

    intake_month = forms.ChoiceField(choices=MONTH_CHOICES, required=True, label="Intake Month")
    intake_year = forms.ChoiceField(
        choices=[(str(year), str(year)) for year in range(datetime.now().year, datetime.now().year + 5)],
        required=True,
        label="Intake Year"
    )
    program = forms.CharField(max_length=255, required=True, label="Study Program")
