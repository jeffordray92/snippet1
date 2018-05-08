from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django import forms


class UploadExcelFileForm(forms.Form):
    file = forms.FileField(label = (_("Choose the Excel file to upload:")))

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file.name.endswith('.xls'):
            raise ValidationError(_
                ('Only .xls files are accepted.'),
                code ='invalid'
            )
