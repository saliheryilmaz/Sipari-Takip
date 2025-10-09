# Django core imports
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

# Local app imports
from . import views
from .views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    ItemSearchListView,
    DeliveryListView,
    DeliveryDetailView,
    DeliveryCreateView,
    DeliveryUpdateView,
    DeliveryDeleteView,
    get_items_ajax_view,
    CategoryListView,
    CategoryDetailView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryDeleteView,
    # Lastik envanteri view'ları
    LastikEnvanteriListView,
    LastikEnvanteriDetailView,
    LastikEnvanteriCreateView,
    LastikEnvanteriUpdateView,
    LastikEnvanteriDeleteView,
    LastikEnvanteriCancelFormView,
    KontrolEdildiListView,
    IptalEdilenLastiklerListView,
    lastik_dashboard,
    whatsapp_gonder,
    lastik_envanteri_cancel,
)

# URL patterns
urlpatterns = [
    # Dashboard
    path('', views.test_view, name='test'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Product URLs
    path(
        'products/',
        ProductListView.as_view(),
        name='productslist'
    ),
    path(
        'product/<slug:slug>/',
        ProductDetailView.as_view(),
        name='product-detail'
    ),
    path(
        'new-product/',
        ProductCreateView.as_view(),
        name='product-create'
    ),
    path(
        'product/<slug:slug>/update/',
        ProductUpdateView.as_view(),
        name='product-update'
    ),
    path(
        'product/<slug:slug>/delete/',
        ProductDeleteView.as_view(),
        name='product-delete'
    ),

    # Item search
    path(
        'search/',
        ItemSearchListView.as_view(),
        name='item_search_list_view'
    ),

    # Delivery URLs
    path(
        'deliveries/',
        DeliveryListView.as_view(),
        name='deliveries'
    ),
    path(
        'delivery/<slug:slug>/',
        DeliveryDetailView.as_view(),
        name='delivery-detail'
    ),
    path(
        'new-delivery/',
        DeliveryCreateView.as_view(),
        name='delivery-create'
    ),
    path(
        'delivery/<int:pk>/update/',
        DeliveryUpdateView.as_view(),
        name='delivery-update'
    ),
    path(
        'delivery/<int:pk>/delete/',
        DeliveryDeleteView.as_view(),
        name='delivery-delete'
    ),

    # AJAX view
    path(
        'get-items/',
        get_items_ajax_view,
        name='get_items'
    ),

    # Category URLs
    path(
        'categories/',
        CategoryListView.as_view(),
        name='category-list'
    ),
    path(
        'categories/<int:pk>/',
        CategoryDetailView.as_view(),
        name='category-detail'
    ),
    path(
        'categories/create/',
        CategoryCreateView.as_view(),
        name='category-create'
    ),
    path(
        'categories/<int:pk>/update/',
        CategoryUpdateView.as_view(),
        name='category-update'
    ),
    path(
        'categories/<int:pk>/delete/',
        CategoryDeleteView.as_view(),
        name='category-delete'
    ),

    path(
        'debug/',
        lambda request: render(request, 'store/debug.html'),
        name='debug'
    ),
    
    
    # Lastik Envanteri URLs
    path(
        'lastik-dashboard/',
        lastik_dashboard,
        name='lastik-dashboard'
    ),
    path(
        'lastik-envanteri/',
        LastikEnvanteriListView.as_view(),
        name='lastik-envanteri-list'
    ),
    path(
        'lastik-envanteri/<int:pk>/',
        LastikEnvanteriDetailView.as_view(),
        name='lastik-envanteri-detail'
    ),
    path(
        'lastik-envanteri/create/',
        LastikEnvanteriCreateView.as_view(),
        name='lastik-envanteri-create'
    ),
    path(
        'lastik-envanteri/<int:pk>/update/',
        LastikEnvanteriUpdateView.as_view(),
        name='lastik-envanteri-update'
    ),
    path(
        'lastik-envanteri/<int:pk>/delete/',
        LastikEnvanteriDeleteView.as_view(),
        name='lastik-envanteri-delete'
    ),
    path(
        'lastik-envanteri/<int:lastik_id>/whatsapp/',
        whatsapp_gonder,
        name='whatsapp-gonder'
    ),
    path(
        'kontrol-edildi/',
        KontrolEdildiListView.as_view(),
        name='kontrol-edildi-list'
    ),
    path(
        'iptal-edilen-lastikler/',
        IptalEdilenLastiklerListView.as_view(),
        name='iptal-edilen-lastikler-list'
    ),
    path(
        'lastik-envanteri/<int:pk>/cancel-form/',
        LastikEnvanteriCancelFormView.as_view(),
        name='lastik-envanteri-cancel-form'
    ),
    path(
        'lastik-envanteri/<int:pk>/cancel/',
        lastik_envanteri_cancel,
        name='lastik-envanteri-cancel'
    ),
]

# Static media files configuration for development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
