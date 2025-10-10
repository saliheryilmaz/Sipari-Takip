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
    
    # Yıl filtresi - URL'den al veya mevcut yılı kullan
    selected_year = request.GET.get('year')
    if not selected_year:
        from datetime import datetime
        selected_year = datetime.now().year
    else:
        selected_year = int(selected_year)
    
    # Yıl aralığı oluştur - timezone aware
    from datetime import datetime
    from django.utils import timezone
    start_date = timezone.make_aware(datetime(selected_year, 1, 1))
    end_date = timezone.make_aware(datetime(selected_year, 12, 31, 23, 59, 59))
    
    # Sadece Admin (AD) ve superuser tüm verileri görebilir
    if current_user.is_superuser or current_user.profile.role == 'AD':
        profiles = Profile.objects.all()
        items = Item.objects.all()
        profiles_count = profiles.count()
    else:
        # Yönetici (EX) ve Operatör (OP) sadece kendi verilerini görür
        profiles = Profile.objects.filter(user=current_user)
        items = Item.objects.filter(user=current_user)
        profiles_count = 1  # Sadece kendisi
    
    Category.objects.annotate(nitem=Count("item"))
    total_items = (
        items.aggregate(Sum("quantity"))
        .get("quantity__sum", 0.00)
    )
    items_count = items.count()

    # Prepare data for charts - kullanıcı bazlı
    if current_user.is_superuser or current_user.profile.role == 'AD':
        category_counts = Category.objects.annotate(
            item_count=Count("item")
        ).values("name", "item_count")
    else:
        category_counts = Category.objects.filter(user=current_user).annotate(
            item_count=Count("item")
        ).values("name", "item_count")
    
    categories = [cat["name"] for cat in category_counts]
    category_counts = [cat["item_count"] for cat in category_counts]

    # Satış verileri - kullanıcı bazlı (soft delete ile) + yıl filtresi
    if current_user.is_superuser or current_user.profile.role == 'AD':
        sale_dates = (
            Sale.objects.filter(
                is_removed=False,
                date_added__date__gte=start_date.date(),
                date_added__date__lte=end_date.date()
            )
            .values("date_added__date")
            .annotate(total_sales=Sum("grand_total"))
            .order_by("date_added__date")
        )
    else:
        sale_dates = (
            Sale.objects.filter(
                user=current_user, 
                is_removed=False,
                date_added__date__gte=start_date.date(),
                date_added__date__lte=end_date.date()
            )
            .values("date_added__date")
            .annotate(total_sales=Sum("grand_total"))
            .order_by("date_added__date")
        )
    sale_dates_labels = [
        date["date_added__date"].strftime("%Y-%m-%d") for date in sale_dates
    ]
    sale_dates_values = [float(date["total_sales"]) for date in sale_dates]

    # Lastik Envanteri verileri - kullanıcı bazlı (soft delete ile) + yıl filtresi + iptal edilenleri hariç tut
    if current_user.is_superuser or current_user.profile.role == 'AD':
        lastik_envanteri = LastikEnvanteri.objects.filter(
            is_removed=False,
            olusturma_tarihi__gte=start_date,
            olusturma_tarihi__lte=end_date
        ).exclude(durum='IPTAL_EDILDI')
    else:
        lastik_envanteri = LastikEnvanteri.objects.filter(
            user=current_user, 
            is_removed=False,
            olusturma_tarihi__gte=start_date,
            olusturma_tarihi__lte=end_date
        ).exclude(durum='IPTAL_EDILDI')
    
    lastik_count = lastik_envanteri.count()
    lastik_total_value = lastik_envanteri.aggregate(Sum("toplam_fiyat"))["toplam_fiyat__sum"] or 0
    
    # Lastik durum dağılımı
    lastik_durum_counts = lastik_envanteri.values("durum").annotate(count=Count("id"))
    lastik_durum_labels = [item["durum"] for item in lastik_durum_counts]
    lastik_durum_values = [item["count"] for item in lastik_durum_counts]
    
    # Lastik marka dağılımı - toplam adet ile
    lastik_marka_counts = lastik_envanteri.values("marka").annotate(total_adet=Sum("adet"))
    lastik_marka_labels = [item["marka"] for item in lastik_marka_counts]
    lastik_marka_values = [item["total_adet"] for item in lastik_marka_counts]
    
    # Lastik ödeme durum dağılımı - toplam fiyat ile
    lastik_odeme_counts = lastik_envanteri.values("odeme").annotate(
        count=Count("id"),
        total_price=Sum("toplam_fiyat")
    )
    lastik_odeme_labels = [item["odeme"] or "Belirtilmemiş" for item in lastik_odeme_counts]
    lastik_odeme_values = [item["count"] for item in lastik_odeme_counts]
    lastik_odeme_prices = [float(item["total_price"] or 0) for item in lastik_odeme_counts]
    
    # Lastik satış verileri - mevsim ve araç tipine göre
    # Doğrudan LastikEnvanteri tablosundan çek - kullanıcı bazlı (soft delete ile) + yıl filtresi + iptal edilenleri hariç tut
    if current_user.is_superuser or current_user.profile.role == 'AD':
        tire_sales_data = LastikEnvanteri.objects.filter(
            is_removed=False,
            durum='KONTROL_EDILDI',  # Kontrol edilmiş lastikler = satışa hazır
            olusturma_tarihi__gte=start_date,
            olusturma_tarihi__lte=end_date
        ).exclude(durum='IPTAL_EDILDI')
    else:
        tire_sales_data = LastikEnvanteri.objects.filter(
            user=current_user,
            is_removed=False,
            durum='KONTROL_EDILDI',  # Kontrol edilmiş lastikler = satışa hazır
            olusturma_tarihi__gte=start_date,
            olusturma_tarihi__lte=end_date
        ).exclude(durum='IPTAL_EDILDI')
    
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
    
    # Cari analizi - en çok alım yaptığımız cariler (fiyat bazında) + yıl filtresi + iptal edilenleri hariç tut
    if current_user.is_superuser or current_user.profile.role == 'AD':
        vendor_purchases = (
            LastikEnvanteri.objects.filter(
                is_removed=False,
                olusturma_tarihi__gte=start_date,
                olusturma_tarihi__lte=end_date
            )
            .exclude(durum='IPTAL_EDILDI')
            .values('cari')
            .annotate(total_purchases=Sum('toplam_fiyat'))
            .order_by('-total_purchases')[:10]  # En çok alım yaptığımız 10 cari
        )
    else:
        vendor_purchases = (
            LastikEnvanteri.objects.filter(
                user=current_user, 
                is_removed=False,
                olusturma_tarihi__gte=start_date,
                olusturma_tarihi__lte=end_date
            )
            .exclude(durum='IPTAL_EDILDI')
            .values('cari')
            .annotate(total_purchases=Sum('toplam_fiyat'))
            .order_by('-total_purchases')[:10]  # En çok alım yaptığımız 10 cari
        )
    
    # Cari verilerini chart için hazırla
    vendor_names = []
    vendor_totals = []
    
    for vendor in vendor_purchases:
        vendor_name = vendor['cari'] or 'İsimsiz Cari'
        vendor_names.append(vendor_name)
        vendor_totals.append(float(vendor['total_purchases'] or 0))

    # Mevcut yıl ve seçili yıl bilgileri
    from datetime import datetime
    current_year = datetime.now().year
    available_years = list(range(current_year - 5, current_year + 2))  # Son 5 yıl + gelecek 2 yıl
    
    context = {
        "items": items,
        "profiles": profiles,
        "profiles_count": profiles_count,
        "items_count": items_count,
        "total_items": total_items,
        "vendors": Vendor.objects.all(),
        "delivery": Delivery.objects.all(),
        "sales": Sale.objects.filter(is_removed=False),
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
        # Cari analizi verileri
        "vendor_names": vendor_names,
        "vendor_totals": vendor_totals,
        # Yıl filtresi verileri
        "selected_year": selected_year,
        "current_year": current_year,
        "available_years": available_years,
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

    def get_queryset(self):
        """Filter items by current user, admin sees all."""
        if self.request.user.is_superuser or self.request.user.profile.role == 'AD':
            return Item.objects.all()
        return Item.objects.filter(user=self.request.user)



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

    def get_form_kwargs(self):
        """Pass user to form for user filtering."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

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

    def get_queryset(self):
        """Filter categories by current user, admin sees all."""
        if self.request.user.is_superuser or self.request.user.profile.role == 'AD':
            return Category.objects.all()
        return Category.objects.filter(user=self.request.user)



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

    def get_form_kwargs(self):
        """Pass user to form for user filtering."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

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
        
        # Kullanıcı bazlı veri izolasyonu - admin tüm verileri görür
        if self.request.user.is_superuser or self.request.user.profile.role == 'AD':
            queryset = LastikEnvanteri.objects.filter(is_removed=False).exclude(durum='KONTROL_EDILDI').exclude(durum='IPTAL_EDILDI')
        else:
            queryset = LastikEnvanteri.objects.filter(user=self.request.user, is_removed=False).exclude(durum='KONTROL_EDILDI').exclude(durum='IPTAL_EDILDI')
        
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

    def get_form_kwargs(self):
        """Pass user to form for user filtering."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Akü veya Jant seçildiğinde mevsim alanını boş bırak
        if form.cleaned_data.get('grup') in ['AKU', 'JANT']:
            form.instance.mevsim = None
        
        # Oluşturan kullanıcıyı ayarla
        form.instance.user = self.request.user
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
        # Akü veya Jant seçildiğinde mevsim alanını boş bırak
        if form.cleaned_data.get('grup') in ['AKU', 'JANT']:
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
    # İstatistikler - Adet sayıları (iptal edilenleri hariç tut)
    toplam_adet = LastikEnvanteri.objects.filter(is_removed=False).exclude(durum='IPTAL_EDILDI').aggregate(
        toplam=Sum('adet')
    )['toplam'] or 0
    
    stok_adet = LastikEnvanteri.objects.filter(is_removed=False, ambar='STOK').exclude(durum='IPTAL_EDILDI').aggregate(
        toplam=Sum('adet')
    )['toplam'] or 0
    
    satis_adet = LastikEnvanteri.objects.filter(is_removed=False, ambar='SATIS').exclude(durum='IPTAL_EDILDI').aggregate(
        toplam=Sum('adet')
    )['toplam'] or 0
    
    yolda_siparis = LastikEnvanteri.objects.filter(is_removed=False, durum='YOLDA').count()
    islem_devam_siparis = LastikEnvanteri.objects.filter(is_removed=False, durum='ISLEM_DEVAM_EDIYOR').count()
    
    # Toplam değer (iptal edilenleri hariç tut)
    toplam_deger = LastikEnvanteri.objects.filter(is_removed=False).exclude(durum='IPTAL_EDILDI').aggregate(
        toplam=Sum('toplam_fiyat')
    )['toplam'] or 0
    
    # Son eklenen lastikler (iptal edilenleri hariç tut)
    son_lastikler = LastikEnvanteri.objects.filter(is_removed=False).exclude(durum='IPTAL_EDILDI').order_by('-olusturma_tarihi')[:10]
    
    # Durum dağılımı (iptal edilenleri hariç tut)
    durum_dagilimi = LastikEnvanteri.objects.filter(is_removed=False).exclude(durum='IPTAL_EDILDI').values('durum').annotate(count=Count('id'))
    
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
        
        # Kullanıcı bazlı veri izolasyonu - admin tüm verileri görür
        if self.request.user.is_superuser or self.request.user.profile.role == 'AD':
            queryset = LastikEnvanteri.objects.filter(is_removed=False, durum='KONTROL_EDILDI')
        else:
            queryset = LastikEnvanteri.objects.filter(user=self.request.user, is_removed=False, durum='KONTROL_EDILDI')
        
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
        
        # Marka dağılımı - KONTROL_EDILDI durumundaki lastikler için (soft delete ile)
        marka_dagilimi = LastikEnvanteri.objects.filter(is_removed=False, durum='KONTROL_EDILDI').values('marka').annotate(
            toplam_adet=Sum('adet')
        ).order_by('-toplam_adet')
        
        # Uppercase'e çevir
        marka_dagilimi = marka_dagilimi.annotate(
            marka_upper=Upper('marka')
        ).values('marka_upper', 'toplam_adet').order_by('-toplam_adet')
        
        context['marka_dagilimi'] = marka_dagilimi
        
        # Ödeme durum dağılımı - KONTROL_EDILDI durumundaki lastikler için (soft delete ile)
        odeme_dagilimi = LastikEnvanteri.objects.filter(is_removed=False, durum='KONTROL_EDILDI').values('odeme').annotate(
            toplam_adet=Sum('adet')
        ).order_by('-toplam_adet')
        
        context['odeme_dagilimi'] = odeme_dagilimi
        
        # Lastik satış analizi - KONTROL_EDILDI durumundaki lastikler için (soft delete ile)
        tire_sales_data = LastikEnvanteri.objects.filter(
            is_removed=False,
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


# İptal işlemi için view'lar
class LastikEnvanteriCancelFormView(LoginRequiredMixin, DetailView):
    """
    İptal sebebi formu görünümü
    """
    model = LastikEnvanteri
    template_name = 'store/lastik_envanteri_cancel.html'
    context_object_name = 'object'
    
    def get_queryset(self):
        """
        Kullanıcı kontrolü ile queryset
        """
        current_user = self.request.user
        if current_user.is_superuser or current_user.profile.role == 'AD':
            return LastikEnvanteri.objects.filter(is_removed=False)
        else:
            return LastikEnvanteri.objects.filter(user=current_user, is_removed=False)
    
    def get(self, request, *args, **kwargs):
        """
        GET isteğini işle
        """
        return super().get(request, *args, **kwargs)


@login_required
def lastik_envanteri_cancel(request, pk):
    """
    Lastik envanteri kaydını iptal et - POST ile sebep al
    """
    if request.method == 'POST':
        try:
            lastik = LastikEnvanteri.objects.get(pk=pk, is_removed=False)
            
            # Kullanıcı kontrolü
            if not request.user.is_superuser and request.user.profile.role != 'AD':
                if lastik.user != request.user:
                    return JsonResponse({'success': False, 'message': 'Bu kaydı iptal etme yetkiniz yok.'})
            
            # İptal sebebini al
            iptal_sebebi = request.POST.get('iptal_sebebi', '').strip()
            
            if not iptal_sebebi or len(iptal_sebebi) < 3:
                return JsonResponse({'success': False, 'message': 'İptal sebebi en az 3 karakter olmalıdır.'})
            
            # Durumu iptal edildi olarak değiştir ve sebebi kaydet
            lastik.durum = 'IPTAL_EDILDI'
            lastik.iptal_sebebi = iptal_sebebi
            lastik.save()
            
            # İptal edilen lastikler sayfasına yönlendir
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            return HttpResponseRedirect(reverse('iptal-edilen-lastikler-list'))
            
        except LastikEnvanteri.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Kayıt bulunamadı.'})
    
    return JsonResponse({'success': False, 'message': 'Geçersiz istek.'})


class IptalEdilenLastiklerListView(LoginRequiredMixin, ListView):
    """
    İptal edilen lastiklerin listesi
    """
    model = LastikEnvanteri
    template_name = 'store/iptal_edilen_lastikler.html'
    context_object_name = 'lastikler'
    paginate_by = 20
    
    def get_queryset(self):
        """
        İptal edilen lastikleri getir
        """
        current_user = self.request.user
        
        if current_user.is_superuser or current_user.profile.role == 'AD':
            return LastikEnvanteri.objects.filter(
                is_removed=False,
                durum='IPTAL_EDILDI'
            ).order_by('-olusturma_tarihi')
        else:
            return LastikEnvanteri.objects.filter(
                user=current_user,
                is_removed=False,
                durum='IPTAL_EDILDI'
            ).order_by('-olusturma_tarihi')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'İptal Edilen Lastikler'
        return context
