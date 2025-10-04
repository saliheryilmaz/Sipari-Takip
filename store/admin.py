"""
Module: admin.py

Django admin configurations for managing categories, items, and deliveries.

This module defines the following admin classes:
- CategoryAdmin: Configuration for the Category model in the admin interface.
- ItemAdmin: Configuration for the Item model in the admin interface.
- DeliveryAdmin: Configuration for the Delivery model in the admin interface.
"""

from django.contrib import admin
from .models import Category, Item, Delivery, Siparis, SiparisKalemi, LastikEnvanteri


class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Category model.
    """
    list_display = ('name', 'slug')
    search_fields = ('name',)
    ordering = ('name',)


class ItemAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Item model.
    """
    list_display = (
        'name', 'brand', 'category', 'quantity', 'price', 'currency', 'expiring_date', 'vendor'
    )
    search_fields = ('name', 'brand', 'category__name', 'vendor__name')
    list_filter = ('category', 'vendor', 'brand', 'currency')
    ordering = ('name',)


class DeliveryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Delivery model.
    """
    list_display = (
        'item', 'customer_name', 'phone_number',
        'location', 'date', 'is_delivered'
    )
    search_fields = ('item__name', 'customer_name')
    list_filter = ('is_delivered', 'date')
    ordering = ('-date',)


# Sipariş kalemleri için inline admin
class SiparisKalemiInline(admin.TabularInline):
    model = SiparisKalemi
    extra = 1
    fields = ('urun', 'adet', 'birim_fiyat', 'toplam_fiyat')
    readonly_fields = ('toplam_fiyat',)


class SiparisAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Siparis model.
    """
    list_display = (
        'siparis_no', 'cari', 'siparis_tarihi', 'durum', 
        'ambar', 'toplam_tutar', 'sms_gonderildi'
    )
    search_fields = ('siparis_no', 'cari__first_name', 'cari__last_name')
    list_filter = ('durum', 'ambar', 'odeme', 'sms_gonderildi', 'siparis_tarihi')
    ordering = ('-siparis_tarihi',)
    inlines = [SiparisKalemiInline]
    readonly_fields = ('toplam_tutar', 'siparis_tarihi')
    
    fieldsets = (
        ('Sipariş Bilgileri', {
            'fields': ('siparis_no', 'cari', 'siparis_tarihi')
        }),
        ('Durum Bilgileri', {
            'fields': ('durum', 'ambar')
        }),
        ('Ödeme ve İletişim', {
            'fields': ('odeme', 'sms_gonderildi')
        }),
        ('Açıklamalar', {
            'fields': ('aciklama1',)
        }),
        ('Toplam', {
            'fields': ('toplam_tutar',)
        }),
    )


class SiparisKalemiAdmin(admin.ModelAdmin):
    """
    Admin configuration for the SiparisKalemi model.
    """
    list_display = ('siparis', 'urun', 'adet', 'birim_fiyat', 'toplam_fiyat')
    search_fields = ('siparis__siparis_no', 'urun__name')
    list_filter = ('siparis__durum', 'urun__category')
    ordering = ('-siparis__siparis_tarihi',)


class LastikEnvanteriAdmin(admin.ModelAdmin):
    """
    Admin configuration for the LastikEnvanteri model.
    """
    list_display = (
        'cari', 'urun', 'marka', 'grup', 'mevsim', 'adet', 
        'birim_fiyat', 'toplam_fiyat', 'durum', 'ambar', 'sms_gonderildi'
    )
    search_fields = ('cari', 'urun', 'marka')
    list_filter = ('grup', 'mevsim', 'durum', 'ambar', 'odeme', 'sms_gonderildi', 'olusturma_tarihi')
    ordering = ('-olusturma_tarihi',)
    readonly_fields = ('toplam_fiyat', 'olusturma_tarihi', 'guncelleme_tarihi')
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('cari', 'urun', 'marka', 'grup', 'mevsim')
        }),
        ('Fiyat Bilgileri', {
            'fields': ('adet', 'birim_fiyat', 'toplam_fiyat')
        }),
        ('Durum Bilgileri', {
            'fields': ('durum', 'ambar')
        }),
        ('Ödeme ve İletişim', {
            'fields': ('odeme', 'sms_gonderildi')
        }),
        ('Açıklamalar', {
            'fields': ('aciklama1',)
        }),
        ('Tarih Bilgileri', {
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Toplam fiyatı otomatik hesapla
        obj.toplam_fiyat = obj.adet * obj.birim_fiyat
        super().save_model(request, obj, form, change)


admin.site.register(Category, CategoryAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Delivery, DeliveryAdmin)
admin.site.register(Siparis, SiparisAdmin)
admin.site.register(SiparisKalemi, SiparisKalemiAdmin)
admin.site.register(LastikEnvanteri, LastikEnvanteriAdmin)
