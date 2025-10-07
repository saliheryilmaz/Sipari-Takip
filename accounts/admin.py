from django.contrib import admin
from .models import Profile, Vendor, Customer


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin interface for the Profile model."""
    list_display = ('user', 'telephone', 'email', 'role', 'status')
    list_filter = ('role', 'status')
    search_fields = ('user__username', 'email', 'first_name', 'last_name')

    def get_queryset(self, request):
        """Admin sees all profiles, regular users see only their own."""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.profile.role == 'AD':
            return qs
        return qs.filter(user=request.user)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """Admin interface for the Vendor model."""
    fields = ('user', 'name', 'phone_number', 'address')
    list_display = ('name', 'user', 'phone_number', 'address', 'is_removed')
    list_filter = ('user', 'is_removed', 'created', 'modified')
    search_fields = ('name', 'phone_number', 'address')

    def get_queryset(self, request):
        """Admin sees all vendors, regular users see only their own."""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.profile.role == 'AD':
            return qs
        return qs.filter(user=request.user)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin interface for the Customer model."""
    list_display = ('first_name', 'last_name', 'user', 'email', 'phone', 'loyalty_points', 'is_removed')
    list_filter = ('user', 'is_removed', 'created', 'modified')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    
    def get_queryset(self, request):
        """Admin sees all customers, regular users see only their own."""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.profile.role == 'AD':
            return qs
        return qs.filter(user=request.user)
