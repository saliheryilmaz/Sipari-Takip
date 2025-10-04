from django.core.management.base import BaseCommand
from store.models import LastikEnvanteri, Category
from accounts.models import Customer


class Command(BaseCommand):
    help = 'Create sample tire data for testing the 3D chart'

    def handle(self, *args, **options):
        # Create sample tire inventory data with different seasons and groups
        sample_data = [
            # Yaz lastikleri - Binek
            {'cari': 'Test Firma 1', 'urun': 'Yaz Lastik 205/55R16', 'marka': 'Bridgestone', 'grup': 'BINEK', 'mevsim': 'YAZ', 'adet': 15, 'birim_fiyat': 1200.00, 'durum': 'TESLIM_EDILDI'},
            {'cari': 'Test Firma 2', 'urun': 'Yaz Lastik 225/45R17', 'marka': 'Michelin', 'grup': 'BINEK', 'mevsim': 'YAZ', 'adet': 8, 'birim_fiyat': 1500.00, 'durum': 'TESLIM_EDILDI'},
            {'cari': 'Test Firma 3', 'urun': 'Yaz Lastik 195/65R15', 'marka': 'Continental', 'grup': 'BINEK', 'mevsim': 'YAZ', 'adet': 12, 'birim_fiyat': 1100.00, 'durum': 'TESLIM_EDILDI'},
            
            # Yaz lastikleri - Ticari
            {'cari': 'Test Firma 4', 'urun': 'Yaz Lastik 225/70R16C', 'marka': 'Goodyear', 'grup': 'TICARI', 'mevsim': 'YAZ', 'adet': 20, 'birim_fiyat': 1800.00, 'durum': 'TESLIM_EDILDI'},
            {'cari': 'Test Firma 5', 'urun': 'Yaz Lastik 245/65R17C', 'marka': 'Pirelli', 'grup': 'TICARI', 'mevsim': 'YAZ', 'adet': 6, 'birim_fiyat': 2000.00, 'durum': 'TESLIM_EDILDI'},
            
            # Kış lastikleri - Binek
            {'cari': 'Test Firma 6', 'urun': 'Kış Lastik 205/55R16', 'marka': 'Bridgestone', 'grup': 'BINEK', 'mevsim': 'KIS', 'adet': 18, 'birim_fiyat': 1300.00, 'durum': 'TESLIM_EDILDI'},
            {'cari': 'Test Firma 7', 'urun': 'Kış Lastik 225/45R17', 'marka': 'Michelin', 'grup': 'BINEK', 'mevsim': 'KIS', 'adet': 10, 'birim_fiyat': 1600.00, 'durum': 'TESLIM_EDILDI'},
            {'cari': 'Test Firma 8', 'urun': 'Kış Lastik 195/65R15', 'marka': 'Continental', 'grup': 'BINEK', 'mevsim': 'KIS', 'adet': 14, 'birim_fiyat': 1200.00, 'durum': 'TESLIM_EDILDI'},
            
            # Kış lastikleri - Ticari
            {'cari': 'Test Firma 9', 'urun': 'Kış Lastik 225/70R16C', 'marka': 'Goodyear', 'grup': 'TICARI', 'mevsim': 'KIS', 'adet': 25, 'birim_fiyat': 1900.00, 'durum': 'TESLIM_EDILDI'},
            {'cari': 'Test Firma 10', 'urun': 'Kış Lastik 245/65R17C', 'marka': 'Pirelli', 'grup': 'TICARI', 'mevsim': 'KIS', 'adet': 8, 'birim_fiyat': 2100.00, 'durum': 'TESLIM_EDILDI'},
            
            # 4 Mevsim lastikleri - Binek
            {'cari': 'Test Firma 11', 'urun': '4 Mevsim Lastik 205/55R16', 'marka': 'Bridgestone', 'grup': 'BINEK', 'mevsim': '4MEVSIM', 'adet': 22, 'birim_fiyat': 1400.00, 'durum': 'TESLIM_EDILDI'},
            {'cari': 'Test Firma 12', 'urun': '4 Mevsim Lastik 225/45R17', 'marka': 'Michelin', 'grup': 'BINEK', 'mevsim': '4MEVSIM', 'adet': 16, 'birim_fiyat': 1700.00, 'durum': 'TESLIM_EDILDI'},
            {'cari': 'Test Firma 13', 'urun': '4 Mevsim Lastik 195/65R15', 'marka': 'Continental', 'grup': 'BINEK', 'mevsim': '4MEVSIM', 'adet': 19, 'birim_fiyat': 1300.00, 'durum': 'TESLIM_EDILDI'},
            
            # 4 Mevsim lastikleri - Ticari
            {'cari': 'Test Firma 14', 'urun': '4 Mevsim Lastik 225/70R16C', 'marka': 'Goodyear', 'grup': 'TICARI', 'mevsim': '4MEVSIM', 'adet': 30, 'birim_fiyat': 2000.00, 'durum': 'TESLIM_EDILDI'},
            {'cari': 'Test Firma 15', 'urun': '4 Mevsim Lastik 245/65R17C', 'marka': 'Pirelli', 'grup': 'TICARI', 'mevsim': '4MEVSIM', 'adet': 12, 'birim_fiyat': 2200.00, 'durum': 'TESLIM_EDILDI'},
        ]
        
        created_count = 0
        for data in sample_data:
            lastik, created = LastikEnvanteri.objects.get_or_create(
                cari=data['cari'],
                urun=data['urun'],
                defaults=data
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created: {data['urun']} - {data['mevsim']} - {data['grup']}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample tire records')
        )
