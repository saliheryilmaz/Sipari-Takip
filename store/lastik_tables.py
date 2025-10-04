import django_tables2 as tables
from .models import LastikEnvanteri

class LastikEnvanteriTable(tables.Table):
    """
    Lastik envanteri tablosu - Excel export için
    """
    
    class Meta:
        model = LastikEnvanteri
        template_name = "django_tables2/semantic.html"
        fields = (
            'cari', 'urun', 'marka', 'grup', 'mevsim', 'adet', 
            'birim_fiyat', 'toplam_fiyat', 'durum', 'ambar', 
            'aciklama1', 'odeme', 'olusturma_tarihi'
        )
        order_by = '-olusturma_tarihi'

