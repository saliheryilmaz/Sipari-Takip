from django import forms
from .models import Item, Category, Delivery, LastikEnvanteri


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
