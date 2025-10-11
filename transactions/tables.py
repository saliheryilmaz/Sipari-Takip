import django_tables2 as tables
from .models import Sale, Purchase


class SaleTable(tables.Table):
    class Meta:
        model = Sale
        template_name = "django_tables2/semantic.html"
        fields = (
            'item',
            'customer_name',
            'transaction_date',
            'payment_method',
            'quantity',
            'price',
            'total_value',
            'amount_received',
            'balance',
            'profile'
        )
        order_by_field = 'sort'


class PurchaseTable(tables.Table):
    class Meta:
        model = Purchase
        template_name = "django_tables2/semantic.html"
        fields = (
            'durum',
            'marka',
            'quantity',
            'urun',
            'dot',
            'giris_tarihi',
            'mevsim',
            'aciklama'
        )
        order_by_field = 'sort'
