"""
Module: store.views

Contains Django views for managing items, profiles,
and deliveries in the store application.

Classes handle product listing, creation, updating,
deletion, and delivery management.
The module integrates with Django's authentication
and querying functionalities.
"""

# Standard library imports
import operator
from functools import reduce

# Django core imports
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Sum
from django import forms

# Authentication and permissions
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Class-based views
from django.views.generic import (
    DetailView, CreateView, UpdateView, DeleteView, ListView
)
from django.views.generic.edit import FormMixin

# Third-party packages
from django_tables2 import SingleTableView
import django_tables2 as tables
from django_tables2.export.views import ExportMixin

# Local app imports
from accounts.models import Profile, Vendor
from transactions.models import Sale
from .models import Category, Item, Delivery, LastikEnvanteri
from .forms import ItemForm, CategoryForm, DeliveryForm
from .tables import ItemTable
from .lastik_tables import LastikEnvanteriTable
from .forms import LastikEnvanteriForm


def test_view(request):
    """Test view for Railway healthcheck - redirect to login"""
    from django.shortcuts import redirect
    return redirect('user-login')

@login_required
def dashboard(request):
    # Kullanıcı veri izolasyonu
    current_user = request.user
    
    # Admin ise tüm verileri göster, değilse sadece kendi verilerini
    if current_user.is_superuser or current_user.profile.role == 'AD':
        profiles = Profile.objects.all()
        items = Item.objects.all()
        profiles_count = profiles.count()
    else:
        # Normal kullanıcı sadece kendi verilerini görür
        profiles = Profile.objects.filter(user=current_user)
        items = Item.objects.filter(created_by=current_user) if hasattr(Item, 'created_by') else Item.objects.none()
        profiles_count = 1  # Sadece kendisi
    
    Category.objects.annotate(nitem=Count("item"))
    total_items = (
        items.aggregate(Sum("quantity"))
        .get("quantity__sum", 0.00)
    )
    items_count = items.count()

    # Prepare data for charts
    category_counts = Category.objects.annotate(
        item_count=Count("item")
    ).values("name", "item_count")
    categories = [cat["name"] for cat in category_counts]
    category_counts = [cat["item_count"] for cat in category_counts]

    sale_dates = (
        Sale.objects.values("date_added__date")
        .annotate(total_sales=Sum("grand_total"))
        .order_by("date_added__date")
    )
    sale_dates_labels = [
        date["date_added__date"].strftime("%Y-%m-%d") for date in sale_dates
    ]
    sale_dates_values = [float(date["total_sales"]) for date in sale_dates]

    # Lastik Envanteri verileri
    lastik_envanteri = LastikEnvanteri.objects.all()
    lastik_count = lastik_envanteri.count()
    lastik_total_value = lastik_envanteri.aggregate(Sum("toplam_fiyat"))["toplam_fiyat__sum"] or 0
    
    # Lastik durum dağılımı
    lastik_durum_counts = lastik_envanteri.values("durum").annotate(count=Count("id"))
    lastik_durum_labels = [item["durum"] for item in lastik_durum_counts]
    lastik_durum_values = [item["count"] for item in lastik_durum_counts]
    
    # Lastik marka dağılımı
    lastik_marka_counts = lastik_envanteri.values("marka").annotate(count=Count("id"))
    lastik_marka_labels = [item["marka"] for item in lastik_marka_counts]
    lastik_marka_values = [item["count"] for item in lastik_marka_counts]
    
    # Lastik ödeme durum dağılımı - toplam fiyat ile
    lastik_odeme_counts = lastik_envanteri.values("odeme").annotate(
        count=Count("id"),
        total_price=Sum("toplam_fiyat")
    )
    lastik_odeme_labels = [item["odeme"] or "Belirtilmemiş" for item in lastik_odeme_counts]
    lastik_odeme_values = [item["count"] for item in lastik_odeme_counts]
    lastik_odeme_prices = [float(item["total_price"] or 0) for item in lastik_odeme_counts]
    
    # Lastik satış verileri - mevsim ve araç tipine göre
    # Doğrudan LastikEnvanteri tablosundan çek
    tire_sales_data = LastikEnvanteri.objects.filter(
        durum='KONTROL_EDILDI'  # Kontrol edilmiş lastikler = satışa hazır
    )
    
    # Mevsim ve grup bazında satış miktarlarını hesapla
    tire_sales_by_season_group = {}
    
    for lastik in tire_sales_data:
        season = lastik.mevsim or 'Belirtilmemiş'
        group = lastik.grup or 'Belirtilmemiş'
        key = f"{season}_{group}"
        
        if key not in tire_sales_by_season_group:
            tire_sales_by_season_group[key] = 0
        tire_sales_by_season_group[key] += lastik.adet
    
    # 3D bar chart için veri hazırla
    seasons = ['Yaz', 'Kış', '4 Mevsim']
    groups = ['Binek', 'Ticari']
    
    # Her mevsim ve grup kombinasyonu için satış miktarını al
    # Binek ve Ticari için ayrı ayrı veri hazırla
    binek_data = []
    ticari_data = []
    
    for season in seasons:
        # Veritabanındaki değerlerle eşleştir
        db_season = 'YAZ' if season == 'Yaz' else ('KIS' if season == 'Kış' else '4MEVSIM')
        
        # Binek verisi
        binek_key = f"{db_season}_BINEK"
        binek_quantity = tire_sales_by_season_group.get(binek_key, 0)
        binek_data.append(binek_quantity)
        
        # Ticari verisi
        ticari_key = f"{db_season}_TICARI"
        ticari_quantity = tire_sales_by_season_group.get(ticari_key, 0)
        ticari_data.append(ticari_quantity)
    
    # Basit liste formatında veri hazırla
    tire_sales_3d_data = [binek_data, ticari_data]
    
    

    context = {
        "items": items,
        "profiles": profiles,
        "profiles_count": profiles_count,
        "items_count": items_count,
        "total_items": total_items,
        "vendors": Vendor.objects.all(),
        "delivery": Delivery.objects.all(),
        "sales": Sale.objects.all(),
        "categories": categories,
        "category_counts": category_counts,
        "sale_dates_labels": sale_dates_labels,
        "sale_dates_values": sale_dates_values,
        # Lastik Envanteri verileri
        "lastik_count": lastik_count,
        "lastik_total_value": lastik_total_value,
        "lastik_durum_labels": lastik_durum_labels,
        "lastik_durum_values": lastik_durum_values,
        "lastik_marka_labels": lastik_marka_labels,
        "lastik_marka_values": lastik_marka_values,
        "lastik_odeme_labels": lastik_odeme_labels,
        "lastik_odeme_values": lastik_odeme_values,
        "lastik_odeme_prices": lastik_odeme_prices,
        # 3D bar chart verileri
        "tire_sales_3d_data": tire_sales_3d_data,
        "seasons": seasons,
        "groups": groups,
    }
    return render(request, "store/dashboard.html", context)


class ProductListView(LoginRequiredMixin, ExportMixin, tables.SingleTableView):
    """
    View class to display a list of products.

    Attributes:
    - model: The model associated with the view.
    - table_class: The table class used for rendering.
    - template_name: The HTML template used for rendering the view.
    - context_object_name: The variable name for the context object.
    - paginate_by: Number of items per page for pagination.
    """

    model = Item
    table_class = ItemTable
    template_name = "store/productslist.html"
    context_object_name = "items"
    paginate_by = 10
    SingleTableView.table_pagination = False


class ItemSearchListView(ProductListView):
    """
    View class to search and display a filtered list of items.

    Attributes:
    - paginate_by: Number of items per page for pagination.
    """

    paginate_by = 10

    def get_queryset(self):
        result = super(ItemSearchListView, self).get_queryset()

        query = self.request.GET.get("q")
        if query:
            query_list = query.split()
            result = result.filter(
                reduce(
                    operator.and_, (Q(name__icontains=q) for q in query_list)
                )
            )
        return result


class ProductDetailView(LoginRequiredMixin, FormMixin, DetailView):
    """
    View class to display detailed information about a product.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    """

    model = Item
    template_name = "store/productdetail.html"

    def get_success_url(self):
        return reverse("product-detail", kwargs={"slug": self.object.slug})


class ProductCreateView(LoginRequiredMixin, CreateView):
    """
    View class to create a new product.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    - form_class: The form class used for data input.
    - success_url: The URL to redirect to upon successful form submission.
    """

    model = Item
    template_name = "store/productcreate.html"
    form_class = ItemForm
    success_url = "/products"

    def test_func(self):
        # item = Item.objects.get(id=pk)
        if self.request.POST.get("quantity") < 1:
            return False
        else:
            return True


class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View class to update product information.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    - fields: The fields to be updated.
    - success_url: The URL to redirect to upon successful form submission.
    """

    model = Item
    template_name = "store/productupdate.html"
    form_class = ItemForm
    success_url = "/products"

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False


class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View class to delete a product.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    - success_url: The URL to redirect to upon successful deletion.
    """

    model = Item
    template_name = "store/productdelete.html"
    success_url = "/products"

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False


class DeliveryListView(
    LoginRequiredMixin, ExportMixin, tables.SingleTableView
):
    """
    View class to display a list of deliveries.

    Attributes:
    - model: The model associated with the view.
    - pagination: Number of items per page for pagination.
    - template_name: The HTML template used for rendering the view.
    - context_object_name: The variable name for the context object.
    """

    model = Delivery
    pagination = 10
    template_name = "store/deliveries.html"
    context_object_name = "deliveries"


class DeliverySearchListView(DeliveryListView):
    """
    View class to search and display a filtered list of deliveries.

    Attributes:
    - paginate_by: Number of items per page for pagination.
    """

    paginate_by = 10

    def get_queryset(self):
        result = super(DeliverySearchListView, self).get_queryset()

        query = self.request.GET.get("q")
        if query:
            query_list = query.split()
            result = result.filter(
                reduce(
                    operator.
                    and_, (Q(customer_name__icontains=q) for q in query_list)
                )
            )
        return result


class DeliveryDetailView(LoginRequiredMixin, DetailView):
    """
    View class to display detailed information about a delivery.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    """

    model = Delivery
    template_name = "store/deliverydetail.html"


class DeliveryCreateView(LoginRequiredMixin, CreateView):
    """
    View class to create a new delivery.

    Attributes:
    - model: The model associated with the view.
    - fields: The fields to be included in the form.
    - template_name: The HTML template used for rendering the view.
    - success_url: The URL to redirect to upon successful form submission.
    """

    model = Delivery
    form_class = DeliveryForm
    template_name = "store/delivery_form.html"
    success_url = "/deliveries"


class DeliveryUpdateView(LoginRequiredMixin, UpdateView):
    """
    View class to update delivery information.

    Attributes:
    - model: The model associated with the view.
    - fields: The fields to be updated.
    - template_name: The HTML template used for rendering the view.
    - success_url: The URL to redirect to upon successful form submission.
    """

    model = Delivery
    form_class = DeliveryForm
    template_name = "store/delivery_form.html"
    success_url = "/deliveries"


class DeliveryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View class to delete a delivery.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    - success_url: The URL to redirect to upon successful deletion.
    """

    model = Delivery
    template_name = "store/productdelete.html"
    success_url = "/deliveries"

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'store/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10
    login_url = 'login'


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = 'store/category_detail.html'
    context_object_name = 'category'
    login_url = 'login'


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    template_name = 'store/category_form.html'
    form_class = CategoryForm
    login_url = 'login'

    def get_success_url(self):
        return reverse_lazy('category-detail', kwargs={'pk': self.object.pk})


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    template_name = 'store/category_form.html'
    form_class = CategoryForm
    login_url = 'login'

    def get_success_url(self):
        return reverse_lazy('category-detail', kwargs={'pk': self.object.pk})


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'store/category_confirm_delete.html'
    context_object_name = 'category'
    success_url = reverse_lazy('category-list')
    login_url = 'login'


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@csrf_exempt
@require_POST
@login_required
def get_items_ajax_view(request):
    if is_ajax(request):
        try:
            term = request.POST.get("term", "")
            data = []

            items = Item.objects.filter(name__icontains=term)
            for item in items[:10]:
                data.append(item.to_json())

            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Not an AJAX request'}, status=400)




# Lastik Envanteri View'ları
class LastikEnvanteriListView(LoginRequiredMixin, ExportMixin, SingleTableView):
    """
    Lastik envanteri listesi görünümü - Fotoğraftaki tabloya uygun
    """
    model = LastikEnvanteri
    template_name = 'store/lastik_envanteri_list.html'
    context_object_name = 'lastikler'
    paginate_by = 20
    login_url = 'login'
    table_class = LastikEnvanteriTable
    table_pagination = False  # Manuel pagination kullanıyoruz
    
    def get_queryset(self):
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        # Kontrol edildi durumundaki lastikleri hariç tut
        queryset = LastikEnvanteri.objects.exclude(durum='KONTROL_EDILDI')
        
        # Filtreleme
        durum = self.request.GET.get('durum')
        if durum:
            queryset = queryset.filter(durum=durum)
            
        cari = self.request.GET.get('cari')
        if cari:
            queryset = queryset.filter(cari__icontains=cari.upper())
            
        marka = self.request.GET.get('marka')
        if marka:
            queryset = queryset.filter(marka__icontains=marka.upper())
            
        grup = self.request.GET.get('grup')
        if grup:
            queryset = queryset.filter(grup=grup)
            
        ambar = self.request.GET.get('ambar')
        if ambar:
            queryset = queryset.filter(ambar=ambar)
            
        # Tarih filtresi
        tarih_filtresi = self.request.GET.get('tarih_filtresi')
        if tarih_filtresi:
            now = timezone.now()
            if tarih_filtresi == '1_ay':
                # Son 1 ay
                start_date = now - timedelta(days=30)
                queryset = queryset.filter(olusturma_tarihi__gte=start_date)
            elif tarih_filtresi == '3_ay':
                # Son 3 ay
                start_date = now - timedelta(days=90)
                queryset = queryset.filter(olusturma_tarihi__gte=start_date)
            elif tarih_filtresi == '6_ay':
                # Son 6 ay
                start_date = now - timedelta(days=180)
                queryset = queryset.filter(olusturma_tarihi__gte=start_date)
            elif tarih_filtresi == 'custom':
                # Özel tarih aralığı
                baslangic_tarihi = self.request.GET.get('baslangic_tarihi')
                bitis_tarihi = self.request.GET.get('bitis_tarihi')
                
                if baslangic_tarihi:
                    try:
                        baslangic_date = datetime.strptime(baslangic_tarihi, '%Y-%m-%d').date()
                        queryset = queryset.filter(olusturma_tarihi__date__gte=baslangic_date)
                    except ValueError:
                        pass
                
                if bitis_tarihi:
                    try:
                        bitis_date = datetime.strptime(bitis_tarihi, '%Y-%m-%d').date()
                        queryset = queryset.filter(olusturma_tarihi__date__lte=bitis_date)
                    except ValueError:
                        pass
            
        return queryset.order_by('-olusturma_tarihi')


class LastikEnvanteriDetailView(LoginRequiredMixin, DetailView):
    """
    Lastik envanteri detay görünümü
    """
    model = LastikEnvanteri
    template_name = 'store/lastik_envanteri_detail.html'
    context_object_name = 'lastik'
    login_url = 'login'


class LastikEnvanteriCreateView(LoginRequiredMixin, CreateView):
    """
    Yeni lastik envanteri oluşturma görünümü
    """
    model = LastikEnvanteri
    form_class = LastikEnvanteriForm
    template_name = 'store/lastik_envanteri_form.html'
    success_url = '/lastik-envanteri'
    login_url = 'login'
    
    def form_valid(self, form):
        # Akü seçildiğinde mevsim alanını boş bırak
        if form.cleaned_data.get('grup') == 'AKU':
            form.instance.mevsim = None
        return super().form_valid(form)
    


class LastikEnvanteriUpdateView(LoginRequiredMixin, UpdateView):
    """
    Lastik envanteri güncelleme görünümü
    """
    model = LastikEnvanteri
    form_class = LastikEnvanteriForm
    template_name = 'store/lastik_envanteri_form.html'
    success_url = '/lastik-envanteri'
    login_url = 'login'
    
    def get_form_class(self):
        # Güncelleme için durum ve sms_gonderildi alanlarını da ekle
        class LastikEnvanteriUpdateForm(LastikEnvanteriForm):
            class Meta(LastikEnvanteriForm.Meta):
                fields = LastikEnvanteriForm.Meta.fields + ['durum', 'sms_gonderildi']
                widgets = LastikEnvanteriForm.Meta.widgets.copy()
                widgets.update({
                    'durum': forms.Select(attrs={'class': 'form-control'}),
                    'sms_gonderildi': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                })
        return LastikEnvanteriUpdateForm
    
    def form_valid(self, form):
        # Akü seçildiğinde mevsim alanını boş bırak
        if form.cleaned_data.get('grup') == 'AKU':
            form.instance.mevsim = None
        return super().form_valid(form)


class LastikEnvanteriDeleteView(LoginRequiredMixin, DeleteView):
    """
    Lastik envanteri silme görünümü
    """
    model = LastikEnvanteri
    template_name = 'store/lastik_envanteri_confirm_delete.html'
    success_url = '/lastik-envanteri'
    login_url = 'login'


@login_required
def lastik_dashboard(request):
    """
    Lastik envanteri ana sayfası
    """
    # İstatistikler - Adet sayıları
    toplam_adet = LastikEnvanteri.objects.aggregate(
        toplam=Sum('adet')
    )['toplam'] or 0
    
    stok_adet = LastikEnvanteri.objects.filter(ambar='STOK').aggregate(
        toplam=Sum('adet')
    )['toplam'] or 0
    
    satis_adet = LastikEnvanteri.objects.filter(ambar='SATIS').aggregate(
        toplam=Sum('adet')
    )['toplam'] or 0
    
    yolda_siparis = LastikEnvanteri.objects.filter(durum='YOLDA').count()
    islem_devam_siparis = LastikEnvanteri.objects.filter(durum='ISLEM_DEVAM_EDIYOR').count()
    
    # Toplam değer
    toplam_deger = LastikEnvanteri.objects.aggregate(
        toplam=Sum('toplam_fiyat')
    )['toplam'] or 0
    
    # Son eklenen lastikler
    son_lastikler = LastikEnvanteri.objects.order_by('-olusturma_tarihi')[:10]
    
    # Durum dağılımı
    durum_dagilimi = LastikEnvanteri.objects.values('durum').annotate(count=Count('id'))
    
    # Marka dağılımı - büyük harfe çevirerek grupla
    from django.db.models import Case, When, Value, CharField
    from django.db.models.functions import Upper
    
    # Önce tüm markaları büyük harfe çevirip grupla - hem kayıt sayısı hem de toplam adet
    marka_dagilimi_raw = LastikEnvanteri.objects.annotate(
        marka_upper=Upper('marka')
    ).values('marka_upper').annotate(
        count=Count('id'),
        toplam_adet=Sum('adet')
    ).order_by('-count')[:10]
    
    # Template için uygun formata çevir
    marka_dagilimi = []
    for item in marka_dagilimi_raw:
        marka_dagilimi.append({
            'marka': item['marka_upper'],
            'count': item['count'],
            'toplam_adet': item['toplam_adet'] or 0
        })
    
    
    context = {
        'toplam_adet': toplam_adet,
        'stok_adet': stok_adet,
        'satis_adet': satis_adet,
        'yolda_siparis': yolda_siparis,
        'islem_devam_siparis': islem_devam_siparis,
        'toplam_deger': toplam_deger,
        'son_lastikler': son_lastikler,
        'durum_dagilimi': durum_dagilimi,
        'marka_dagilimi': marka_dagilimi,
    }
    
    return render(request, 'store/lastik_dashboard.html', context)


@login_required
def whatsapp_gonder(request, lastik_id):
    """
    WhatsApp mesaj gönderme fonksiyonu
    """
    from django.utils import timezone
    
    try:
        lastik = LastikEnvanteri.objects.get(id=lastik_id)
        
        # Tarihi doğru timezone ile formatla
        guncelleme_tarihi = timezone.localtime(lastik.guncelleme_tarihi)
        
        # WhatsApp mesajı oluştur
        mesaj = f"""
*MesTakip - {lastik.cari}*

*Ürün:* {lastik.urun}
*Marka:* {lastik.marka}
*Adet:* {lastik.adet}
*Durum:* {lastik.get_durum_display()}
*Güncellenen Son Tarih:* {guncelleme_tarihi.strftime('%d.%m.%Y %H:%M')}
        """
        
        # WhatsApp URL oluştur
        mesaj_encoded = mesaj.replace(' ', '%20').replace('\n', '%0A')
        whatsapp_url = f"https://wa.me/?text={mesaj_encoded}"
        
        # SMS gönderildi olarak işaretle
        lastik.sms_gonderildi = True
        lastik.save()
        
        return JsonResponse({
            'success': True,
            'whatsapp_url': whatsapp_url,
            'message': 'WhatsApp mesajı hazırlandı'
        })
        
    except LastikEnvanteri.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Lastik bulunamadı'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Hata: {str(e)}'
        })


class KontrolEdildiListView(LoginRequiredMixin, ExportMixin, SingleTableView):
    """
    Kontrol edildi durumundaki lastikleri listeler
    """
    model = LastikEnvanteri
    template_name = 'store/kontrol_edildi.html'
    context_object_name = 'lastikler'
    paginate_by = 10
    login_url = 'login'
    table_class = LastikEnvanteriTable
    table_pagination = False

    def get_queryset(self):
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        # Sadece kontrol edildi durumundaki lastikleri al
        queryset = LastikEnvanteri.objects.filter(durum='KONTROL_EDILDI')
        
        # Filtreleme
        cari = self.request.GET.get('cari')
        if cari:
            queryset = queryset.filter(cari__icontains=cari.upper())
            
        marka = self.request.GET.get('marka')
        if marka:
            queryset = queryset.filter(marka__icontains=marka.upper())
            
        grup = self.request.GET.get('grup')
        if grup:
            queryset = queryset.filter(grup=grup)
            
        mevsim = self.request.GET.get('mevsim')
        if mevsim:
            queryset = queryset.filter(mevsim=mevsim)
            
        ambar = self.request.GET.get('ambar')
        if ambar:
            queryset = queryset.filter(ambar=ambar)
            
        # Tarih filtresi
        tarih_filtresi = self.request.GET.get('tarih_filtresi')
        if tarih_filtresi:
            now = timezone.now()
            if tarih_filtresi == '1_ay':
                # Son 1 ay
                start_date = now - timedelta(days=30)
                queryset = queryset.filter(olusturma_tarihi__gte=start_date)
            elif tarih_filtresi == '3_ay':
                # Son 3 ay
                start_date = now - timedelta(days=90)
                queryset = queryset.filter(olusturma_tarihi__gte=start_date)
            elif tarih_filtresi == '6_ay':
                # Son 6 ay
                start_date = now - timedelta(days=180)
                queryset = queryset.filter(olusturma_tarihi__gte=start_date)
            elif tarih_filtresi == 'custom':
                # Özel tarih aralığı
                baslangic_tarihi = self.request.GET.get('baslangic_tarihi')
                bitis_tarihi = self.request.GET.get('bitis_tarihi')
                
                if baslangic_tarihi:
                    try:
                        baslangic_date = datetime.strptime(baslangic_tarihi, '%Y-%m-%d').date()
                        queryset = queryset.filter(olusturma_tarihi__date__gte=baslangic_date)
                    except ValueError:
                        pass
                
                if bitis_tarihi:
                    try:
                        bitis_date = datetime.strptime(bitis_tarihi, '%Y-%m-%d').date()
                        queryset = queryset.filter(olusturma_tarihi__date__lte=bitis_date)
                    except ValueError:
                        pass
            
        return queryset.order_by('-olusturma_tarihi')
    
    def get_context_data(self, **kwargs):
        from django.db.models.functions import Upper
        
        context = super().get_context_data(**kwargs)
        
        # Marka dağılımı - KONTROL_EDILDI durumundaki lastikler için
        marka_dagilimi = LastikEnvanteri.objects.filter(durum='KONTROL_EDILDI').values('marka').annotate(
            toplam_adet=Sum('adet')
        ).order_by('-toplam_adet')
        
        # Uppercase'e çevir
        marka_dagilimi = marka_dagilimi.annotate(
            marka_upper=Upper('marka')
        ).values('marka_upper', 'toplam_adet').order_by('-toplam_adet')
        
        context['marka_dagilimi'] = marka_dagilimi
        
        # Ödeme durum dağılımı - KONTROL_EDILDI durumundaki lastikler için
        odeme_dagilimi = LastikEnvanteri.objects.filter(durum='KONTROL_EDILDI').values('odeme').annotate(
            toplam_adet=Sum('adet')
        ).order_by('-toplam_adet')
        
        context['odeme_dagilimi'] = odeme_dagilimi
        
        # Lastik satış analizi - KONTROL_EDILDI durumundaki lastikler için
        tire_sales_data = LastikEnvanteri.objects.filter(
            durum='KONTROL_EDILDI'  # Kontrol edilmiş lastikler
        )
        tire_sales_by_season_group = {}
        for lastik in tire_sales_data:
            season = lastik.mevsim or 'Belirtilmemiş'
            group = lastik.grup or 'Belirtilmemiş'
            key = f"{season}_{group}"
            if key not in tire_sales_by_season_group:
                tire_sales_by_season_group[key] = 0
            tire_sales_by_season_group[key] += lastik.adet
        
        seasons = ['Yaz', 'Kış', '4 Mevsim']
        groups = ['Binek', 'Ticari']
        binek_data = []
        ticari_data = []
        
        for season in seasons:
            db_season = 'YAZ' if season == 'Yaz' else ('KIS' if season == 'Kış' else '4MEVSIM')
            binek_key = f"{db_season}_BINEK"
            binek_quantity = tire_sales_by_season_group.get(binek_key, 0)
            binek_data.append(binek_quantity)
            
            ticari_key = f"{db_season}_TICARI"
            ticari_quantity = tire_sales_by_season_group.get(ticari_key, 0)
            ticari_data.append(ticari_quantity)
        
        tire_sales_3d_data = [binek_data, ticari_data]
        context['seasons'] = seasons
        context['tire_sales_3d_data'] = tire_sales_3d_data
        
        return context
