"""
Module: admin.py

Django admin configurations for managing categories, items, and deliveries.

This module defines the following admin classes:
- CategoryAdmin: Configuration for the Category model in the admin interface.
- ItemAdmin: Configuration for the Item model in the admin interface.
- DeliveryAdmin: Configuration for the Delivery model in the admin interface.
"""

from django.contrib import admin
from .models import Category, Item, Delivery, LastikEnvanteri


class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Category model.
    """
    list_display = ('name', 'user', 'slug')
    list_filter = ('user',)
    search_fields = ('name',)
    ordering = ('name',)

    def get_queryset(self, request):
        """Admin sees all categories, regular users see only their own."""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.profile.role == 'AD':
            return qs
        return qs.filter(user=request.user)


class ItemAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Item model.
    """
    list_display = (
        'name', 'user', 'brand', 'category', 'quantity', 'price', 'currency', 'expiring_date', 'vendor'
    )
    search_fields = ('name', 'brand', 'category__name', 'vendor__name')
    list_filter = ('user', 'category', 'vendor', 'brand', 'currency')
    ordering = ('name',)

    def get_queryset(self, request):
        """Admin sees all items, regular users see only their own."""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.profile.role == 'AD':
            return qs
        return qs.filter(user=request.user)


class DeliveryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Delivery model.
    """
    list_display = (
        'item', 'user', 'customer_name', 'phone_number',
        'location', 'date', 'is_delivered'
    )
    search_fields = ('item__name', 'customer_name')
    list_filter = ('user', 'is_delivered', 'date')
    ordering = ('-date',)

    def get_queryset(self, request):
        """Admin sees all deliveries, regular users see only their own."""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.profile.role == 'AD':
            return qs
        return qs.filter(user=request.user)


class LastikEnvanteriAdmin(admin.ModelAdmin):
    """
    Admin configuration for the LastikEnvanteri model.
    """
    list_display = (
        'cari', 'user', 'urun', 'marka', 'grup', 'mevsim', 'adet', 
        'birim_fiyat', 'toplam_fiyat', 'durum', 'ambar', 'sms_gonderildi'
    )
    search_fields = ('cari', 'urun', 'marka')
    list_filter = ('user', 'grup', 'mevsim', 'durum', 'ambar', 'odeme', 'sms_gonderildi', 'olusturma_tarihi')
    ordering = ('-olusturma_tarihi',)
    readonly_fields = ('toplam_fiyat', 'olusturma_tarihi', 'guncelleme_tarihi')
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('cari', 'user', 'urun', 'marka', 'grup', 'mevsim')
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
    
    def get_queryset(self, request):
        """Admin sees all lastik envanteri, regular users see only their own."""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.profile.role == 'AD':
            return qs
        return qs.filter(user=request.user)
    
    def save_model(self, request, obj, form, change):
        # Toplam fiyatı otomatik hesapla
        obj.toplam_fiyat = obj.adet * obj.birim_fiyat
        super().save_model(request, obj, form, change)


admin.site.register(Category, CategoryAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Delivery, DeliveryAdmin)
admin.site.register(LastikEnvanteri, LastikEnvanteriAdmin)
