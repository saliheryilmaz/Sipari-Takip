from django import forms
from .models import Item, Category, Delivery, LastikEnvanteri
from accounts.models import Vendor


class ItemForm(forms.ModelForm):
    """
    A form for creating or updating an Item in the inventory.
    """
    class Meta:
        model = Item
        fields = [
            'name',
            'description',
            'category',
            'quantity',
            'price',
            'expiring_date',
            'vendor'
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Kullanıcı bazlı filtreleme
        if self.user:
            self.fields['category'].queryset = Category.objects.filter(user=self.user)
            self.fields['vendor'].queryset = Vendor.objects.filter(user=self.user)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2
                }
            ),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01'
                }
            ),
            'expiring_date': forms.DateTimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'datetime-local'
                }
            ),
            'vendor': forms.Select(attrs={'class': 'form-control'}),
        }


class CategoryForm(forms.ModelForm):
    """
    A form for creating or updating category.
    """
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name',
                'aria-label': 'Category Name'
            }),
        }
        labels = {
            'name': 'Category Name',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance



class DeliveryForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = [
            'item',
            'customer_name',
            'phone_number',
            'location',
            'date',
            'is_delivered'
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select item',
            }),
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter customer name',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter delivery location',
            }),
            'date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'placeholder': 'Select delivery date and time',
                'type': 'datetime-local'
            }),
            'is_delivered': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'label': 'Mark as delivered',
            }),
        }


class LastikEnvanteriForm(forms.ModelForm):
    """
    Lastik Envanteri için özel form
    """
    class Meta:
        model = LastikEnvanteri
        fields = ['cari', 'urun', 'marka', 'grup', 'mevsim', 'adet', 'birim_fiyat', 'toplam_fiyat',
                  'ambar', 'aciklama1', 'odeme', 'one_cikar']
        widgets = {
            'cari': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Müşteri firma adını girin',
                'maxlength': '100'
            }),
            'urun': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Lastik model ve özelliklerini girin'
            }),
            'marka': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Lastik markasını girin'
            }),
            'grup': forms.Select(attrs={
                'class': 'form-control'
            }),
            'mevsim': forms.Select(attrs={
                'class': 'form-control'
            }),
            'adet': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adet girin veya otomatik hesaplanır',
                'step': '1',
                'min': '0'
            }),
            'birim_fiyat': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bir lastiğin fiyatını girin',
                'step': '0.01'
            }),
            'toplam_fiyat': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Toplam tutarı girin (adet otomatik hesaplanır)',
                'step': '0.01'
            }),
            'ambar': forms.Select(attrs={
                'class': 'form-control'
            }),
            'aciklama1': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Ek açıklama girin',
                'rows': '3'
            }),
            'odeme': forms.Select(attrs={
                'class': 'form-control'
            }),
            'one_cikar': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Operatörler sadece temel alanları görebilir
        if self.user and self.user.profile.role == 'OP':
            # Operatörler için sadece temel alanları göster
            allowed_fields = ['cari', 'urun', 'marka', 'grup', 'mevsim', 'adet', 'birim_fiyat', 'ambar', 'aciklama1']
            for field_name in self.fields:
                if field_name not in allowed_fields:
                    self.fields[field_name].widget = forms.HiddenInput()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance

