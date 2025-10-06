from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create a superuser for Railway deployment'

    def handle(self, *args, **options):
        # Admin kullanıcısını oluştur veya güncelle
        if User.objects.filter(username='admin').exists():
            admin_user = User.objects.get(username='admin')
            admin_user.set_password('admin123')
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.save()
            self.stdout.write(
                self.style.SUCCESS('Admin user updated successfully!')
            )
        else:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@mestakip.com',
                password='admin123'
            )
            self.stdout.write(
                self.style.SUCCESS('Admin user created successfully!')
            )
        
        # Profile oluştur
        from accounts.models import Profile
        if not Profile.objects.filter(user=admin_user).exists():
            Profile.objects.create(
                user=admin_user,
                role='AD',
                status='A'
            )
            self.stdout.write('Admin profile created!')
        
        self.stdout.write('Username: admin')
        self.stdout.write('Password: admin123')
        self.stdout.write('Email: admin@mestakip.com')
