from django import forms
from .models import Property, PropertyImage, PropertyType, City, State,UserProfile
from django.contrib.auth.models import User


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'property_type', 'price', 
            'bedrooms', 'bathrooms', 'area', 'address', 
            'city', 'state', 'owner_phone', 'main_image', 'is_published'
        ]
        widgets = {
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'state': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active options
        self.fields['property_type'].queryset = PropertyType.objects.filter(is_active=True)
        self.fields['city'].queryset = City.objects.filter(is_active=True)
        self.fields['state'].queryset = State.objects.filter(is_active=True)


class PropertyImageForm(forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ['image']



class UserRoleForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        label="الدور",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = UserProfile
        fields = ['role']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'] = forms.ModelChoiceField(
            queryset=User.objects.all(),
            label="المستخدم",
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        if self.instance and self.instance.pk:
            self.fields['user'].initial = self.instance.user
            self.fields['user'].disabled = True

class UserRoleUpdateForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="المستخدم",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        label="الدور",
        widget=forms.Select(attrs={'class': 'form-select'})
    )