from django import forms


class FileUploadForm(forms.Form):
    file = forms.FileField(
        label="Upload Menu File",
        help_text="Upload a CSV or Excel file containing the menu."
    )
