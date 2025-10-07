from django.contrib import admin
from .models import Sale, SaleDetail, Purchase


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for the Sale model.
    """
    list_display = (
        'id',
        'user',
        'customer',
        'date_added',
        'grand_total',
        'amount_paid',
        'amount_change'
    )
    search_fields = ('customer__first_name', 'customer__last_name', 'id')
    list_filter = ('user', 'date_added', 'customer')
    ordering = ('-date_added',)
    readonly_fields = ('date_added',)
    date_hierarchy = 'date_added'

    def get_queryset(self, request):
        """Admin sees all sales, regular users see only their own."""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.profile.role == 'AD':
            return qs
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        """
        Save the Sale instance, overriding the default save behavior.
        """
        super().save_model(request, obj, form, change)


@admin.register(SaleDetail)
class SaleDetailAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for the SaleDetail model.
    """
    list_display = (
        'id',
        'sale',
        'item',
        'price',
        'quantity',
        'total_detail'
    )
    search_fields = ('sale__id', 'item__name')
    list_filter = ('sale', 'item')
    ordering = ('sale', 'item')

    def save_model(self, request, obj, form, change):
        """
        Save the SaleDetail instance, overriding the default save behavior.
        """
        super().save_model(request, obj, form, change)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for the Purchase model.
    """
    list_display = (
        'slug',
        'user',
        'item',
        'vendor',
        'order_date',
        'delivery_date',
        'quantity',
        'price',
        'total_value',
        'delivery_status'
    )
    search_fields = ('item__name', 'vendor__name', 'slug')
    list_filter = ('user', 'order_date', 'vendor', 'delivery_status')
    ordering = ('-order_date',)
    readonly_fields = ('total_value',)

    def get_queryset(self, request):
        """Admin sees all purchases, regular users see only their own."""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.profile.role == 'AD':
            return qs
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        """
        Save the Purchase instance and compute the total value.
        """
        obj.total_value = obj.price * obj.quantity
        super().save_model(request, obj, form, change)
