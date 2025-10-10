"""
Module: models.py

Contains Django models for handling categories, items, and deliveries.

This module defines the following classes:
- Category: Represents a category for items.
- Item: Represents an item in the inventory.
- Delivery: Represents a delivery of an item to a customer.

Each class provides specific fields and methods for handling related data.
"""

from django.db import models
from django.urls import reverse
from django.forms import model_to_dict
from django_extensions.db.fields import AutoSlugField
from phonenumber_field.modelfields import PhoneNumberField
from model_utils.models import TimeStampedModel, SoftDeletableModel
from accounts.models import Vendor, Customer


class Category(models.Model):
    """
    Ürünler için kategoriyi temsil eder.
    """
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Kullanıcı')
    name = models.CharField(max_length=50, verbose_name='Kategori Adı')
    slug = AutoSlugField(unique=True, populate_from='name')

    def __str__(self):
        """
        Kategorinin string temsili.
        """
        return f"Kategori: {self.name}"

    class Meta:
        verbose_name = 'Kategori'
        verbose_name_plural = 'Kategoriler'


class Item(models.Model):
    """
    Envanterdeki bir ürünü temsil eder.
    """
    GRUP_CHOICES = [
        ('BINEK', 'Binek'),
        ('TICARI', 'Ticari'),
        ('AKU', 'Akü'),
    ]
    
    MEVSIM_CHOICES = [
        ('YAZ', 'Yaz'),
        ('KIS', 'Kış'),
        ('4MEVSIM', '4 Mevsim'),
    ]
    
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Kullanıcı')
    slug = AutoSlugField(unique=True, populate_from='name')
    name = models.CharField(max_length=200, verbose_name='Ürün Adı')
    description = models.TextField(max_length=256, blank=True, null=True, verbose_name='Açıklama')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Kategori')
    quantity = models.IntegerField(default=0, verbose_name='Adet')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Birim Fiyat')
    expiring_date = models.DateTimeField(null=True, blank=True, verbose_name='Son Kullanma Tarihi')
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, verbose_name='Tedarikçi')
    
    # Lastik özellikleri
    brand = models.CharField(max_length=100, blank=True, null=True, verbose_name='Marka')
    group = models.CharField(max_length=50, choices=GRUP_CHOICES, blank=True, null=True, verbose_name='Grup')
    season = models.CharField(max_length=20, choices=MEVSIM_CHOICES, blank=True, null=True, verbose_name='Mevsim')
    currency = models.CharField(max_length=3, default='TRY', choices=[('TRY', '₺'), ('USD', '$')], verbose_name='Para Birimi')

    def __str__(self):
        """
        String representation of the item.
        """
        return (
            f"{self.name} - Category: {self.category}, "
            f"Quantity: {self.quantity}"
        )

    def get_absolute_url(self):
        """
        Returns the absolute URL for an item detail view.
        """
        return reverse('item-detail', kwargs={'slug': self.slug})

    def to_json(self):
        product = model_to_dict(self)
        product['id'] = self.id
        product['text'] = self.name
        product['category'] = self.category.name
        product['quantity'] = 1
        product['total_product'] = 0
        return product

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Items'


class Delivery(models.Model):
    """
    Müşteriye ürün teslimatını temsil eder.
    """
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Kullanıcı')
    item = models.ForeignKey(
        Item, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Ürün'
    )
    customer_name = models.CharField(max_length=30, blank=True, null=True, verbose_name='Müşteri Adı')
    phone_number = PhoneNumberField(blank=True, null=True, verbose_name='Telefon Numarası')
    location = models.CharField(max_length=20, blank=True, null=True, verbose_name='Konum')
    date = models.DateTimeField(verbose_name='Tarih')
    is_delivered = models.BooleanField(
        default=False, verbose_name='Teslim Edildi'
    )

    def __str__(self):
        """
        Teslimatın string temsili.
        """
        return (
            f"{self.item} ürününün {self.customer_name} müşterisine "
            f"{self.location} konumunda {self.date} tarihinde teslimatı"
        )


# Lastik envanter sistemi - Fotoğraftaki tabloya uygun
class LastikEnvanteri(SoftDeletableModel, TimeStampedModel):
    """
    Fotoğraftaki Excel tablosuna uygun lastik envanter modeli
    """
    DURUM_CHOICES = [
        ('YOLDA', 'Yolda'),
        ('ISLEM_DEVAM_EDIYOR', 'İşlem Devam Ediyor'),
        ('TESLIM_EDILDI', 'Teslim Edildi'),
        ('KONTROL_EDILDI', 'Kontrol Edildi'),
        ('IPTAL_EDILDI', 'İptal Edildi'),
    ]
    
    
    AMBAR_CHOICES = [
        ('SATIS', 'Satış'),
        ('STOK', 'Stok'),
    ]
    
    
    ODEME_CHOICES = [
        ('KART', 'Kredi Kartı'),
        ('HAVALE', 'Havale'),
        ('CARI_HESAP', 'Cari Hesap'),
    ]
    
    GRUP_CHOICES = [
        ('BINEK', 'Binek'),
        ('TICARI', 'Ticari'),
        ('AKU', 'Akü'),
        ('JANT', 'Jant'),
    ]
    
    MEVSIM_CHOICES = [
        ('YAZ', 'Yaz'),
        ('KIS', 'Kış'),
        ('4MEVSIM', '4 Mevsim'),
    ]
    
    # Ana alanlar
    cari = models.CharField(max_length=100, verbose_name='Cari (Firma)')
    urun = models.CharField(max_length=200, verbose_name='Ürün (Lastik Marka Model)')
    marka = models.CharField(max_length=100, verbose_name='Marka')
    grup = models.CharField(max_length=20, choices=GRUP_CHOICES, verbose_name='Grup')
    mevsim = models.CharField(max_length=20, choices=MEVSIM_CHOICES, verbose_name='Mevsim')
    adet = models.IntegerField(default=1, verbose_name='Adet')
    birim_fiyat = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Birim Fiyat')
    toplam_fiyat = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Toplam Fiyat')
    durum = models.CharField(max_length=20, choices=DURUM_CHOICES, default='YOLDA', verbose_name='Durum')
    ambar = models.CharField(max_length=20, choices=AMBAR_CHOICES, default='STOK', verbose_name='Ambar')
    aciklama1 = models.TextField(blank=True, null=True, verbose_name='Açıklama 1')
    odeme = models.CharField(max_length=20, choices=ODEME_CHOICES, blank=True, null=True, verbose_name='Ödeme')
    sms_gonderildi = models.BooleanField(default=False, verbose_name='SMS Gönderildi')
    one_cikar = models.BooleanField(default=False, verbose_name='Öne Çıkar')
    iptal_sebebi = models.TextField(blank=True, null=True, verbose_name='İptal Sebebi')
    
    # Kullanıcı alanı - veri izolasyonu için
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Kullanıcı')
    
    # Tarih alanları
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturma Tarihi')
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name='Güncelleme Tarihi')
    
    def save(self, *args, **kwargs):
        # Durum otomatik olarak YOLDA olarak ayarla
        if not self.durum:
            self.durum = 'YOLDA'
        
        # Adet otomatik hesapla (toplam fiyat / birim fiyat)
        if self.toplam_fiyat and self.birim_fiyat and self.birim_fiyat > 0:
            self.adet = round(self.toplam_fiyat / self.birim_fiyat)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.cari} - {self.urun} ({self.adet} adet)"
    
    class Meta:
        verbose_name = 'Lastik Envanteri'
        verbose_name_plural = 'Lastik Envanteri'
        ordering = ['-olusturma_tarihi']
