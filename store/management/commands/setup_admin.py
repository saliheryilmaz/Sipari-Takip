from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile

class Command(BaseCommand):
    help = 'Setup admin user for MESTakip'

    def handle(self, *args, **options):
        # Admin kullanıcısını oluştur
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@mestakip.com',
                'is_superuser': True,
                'is_staff': True,
                'is_active': True
            }
        )
        
        # Şifreyi güncelle
        admin_user.set_password('admin123')
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.is_active = True
        admin_user.save()
        
        # Profile oluştur
        profile, profile_created = Profile.objects.get_or_create(
            user=admin_user,
            defaults={
                'role': 'AD',
                'status': 'A'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('✅ Admin user created successfully!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Admin user updated successfully!')
            )
        
        if profile_created:
            self.stdout.write('✅ Admin profile created!')
        else:
            self.stdout.write('✅ Admin profile updated!')
        
        self.stdout.write('')
        self.stdout.write('🔑 Login Bilgileri:')
        self.stdout.write('Username: admin')
        self.stdout.write('Password: admin123')
        self.stdout.write('Email: admin@mestakip.com')
        self.stdout.write('')
        self.stdout.write('🌐 Siteye gidin ve giriş yapın!')
