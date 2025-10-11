from django import forms
from .models import Purchase


class BootstrapMixin(forms.ModelForm):
    """
    A mixin to add Bootstrap classes to form fields.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class PurchaseForm(BootstrapMixin, forms.ModelForm):
    """
    A form for creating and updating Purchase instances.
    """
    class Meta:
        model = Purchase
        fields = [
            'durum', 'marka', 'quantity', 'urun', 'dot', 'giris_tarihi', 'mevsim', 'aciklama'
        ]
        labels = {
            'durum': 'Durum',
            'marka': 'Marka',
            'quantity': 'Adet',
            'urun': 'Ürün (Lastik Marka Model)',
            'dot': 'DOT (Yıl)',
            'giris_tarihi': 'Giriş Tarihi',
            'mevsim': 'Mevsim',
            'aciklama': 'Detaylı Açıklama',
        }
        help_texts = {
            'durum': 'Lastiğin genel durumunu seçin',
            'marka': 'Lastik markasını girin',
            'quantity': 'Lastik adet sayısını girin',
            'urun': 'Lastik marka ve modelini girin',
            'dot': 'Lastik üretim yılını girin (örn: 2025)',
            'giris_tarihi': 'Lastiğin depoya giriş tarihini seçin',
            'mevsim': 'Lastik mevsimini seçin',
            'aciklama': 'Ek notlar ve açıklamalar',
        }
        widgets = {
            'giris_tarihi': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'datetime-local'
                }
            ),
            'aciklama': forms.Textarea(
                attrs={'rows': 3, 'cols': 40, 'placeholder': 'Detaylı açıklama ve notlar...'}
            ),
            'quantity': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Adet sayısı'}
            ),
            'durum': forms.Select(
                attrs={'class': 'form-control'}
            ),
            'marka': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Örn: Michelin, Bridgestone...'}
            ),
            'urun': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Örn: Michelin Pilot Sport 4 225/45R17'}
            ),
            'dot': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '2025', 'maxlength': '4', 'pattern': '[0-9]{4}'}
            ),
            'mevsim': forms.Select(
                attrs={'class': 'form-control'}
            ),
        }
