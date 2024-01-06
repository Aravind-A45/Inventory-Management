from django import forms
from .models import *

class NewCategoryForm(forms.ModelForm):
  class Meta:
    model = Category
    fields = ('name',)

    widgets = {
      'name': forms.TextInput(attrs={
        'placeholder': 'Enter the Category',
      }),
    }
