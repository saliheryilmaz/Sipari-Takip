# 🚀 MESTakip - Inventory Management System Deployment Guide

## 📋 Deployment Seçenekleri

### 1. 🟢 Railway (Önerilen - Ücretsiz)
```bash
# 1. Railway hesabı oluşturun: https://railway.app
# 2. GitHub repository'nizi bağlayın
# 3. Otomatik deploy başlayacak
# 4. PostgreSQL database ekleyin
# 5. Environment variables ayarlayın:
#    - SECRET_KEY: Güvenli bir key oluşturun
#    - DEBUG: False
#    - DATABASE_URL: Otomatik oluşturulacak
```

### 2. 🔵 Render (Ücretsiz)
```bash
# 1. Render hesabı oluşturun: https://render.com
# 2. "New Web Service" seçin
# 3. GitHub repository'nizi bağlayın
# 4. Build Command: pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
# 5. Start Command: gunicorn InventoryMS.wsgi:application
# 6. PostgreSQL database ekleyin
```

### 3. 🟣 Heroku (Ücretli)
```bash
# 1. Heroku CLI kurun
# 2. Heroku hesabı oluşturun
heroku login
heroku create mestakip-inventory
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

### 4. 🟠 Vercel (Ücretsiz)
```bash
# 1. Vercel hesabı oluşturun: https://vercel.com
# 2. GitHub repository'nizi bağlayın
# 3. Otomatik deploy başlayacak
# 4. PostgreSQL database ekleyin (Vercel Postgres)
```

## 🔧 Environment Variables

Production ortamında şu environment variables'ları ayarlayın:

```env
DEBUG=False
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:password@host:port/database
```

## 📦 Gerekli Adımlar

### 1. Static Files
```bash
python manage.py collectstatic --noinput
```

### 2. Database Migration
```bash
python manage.py migrate
```

### 3. Superuser Oluşturma
```bash
python manage.py createsuperuser
```

## 🌐 Domain Ayarları

Kendi domain'inizi kullanmak istiyorsanız:

1. `InventoryMS/settings.py` dosyasında `ALLOWED_HOSTS` listesine domain'inizi ekleyin
2. DNS ayarlarınızı deployment platformunuza yönlendirin

## 🔒 Güvenlik

- ✅ HTTPS zorunlu
- ✅ Güvenli session cookies
- ✅ CSRF koruması
- ✅ XSS koruması
- ✅ Güvenli başlıklar

## 📊 Monitoring

Production ortamında monitoring için:
- Railway: Built-in metrics
- Render: Built-in monitoring
- Heroku: Heroku Metrics
- Vercel: Vercel Analytics

## 🆘 Sorun Giderme

### Static Files Yüklenmiyor
```bash
python manage.py collectstatic --noinput
```

### Database Bağlantı Hatası
- DATABASE_URL environment variable'ını kontrol edin
- Database servisinin çalıştığından emin olun

### 500 Internal Server Error
- DEBUG=True yaparak detaylı hata mesajını görün
- Log dosyalarını kontrol edin

## 📞 Destek

Herhangi bir sorun yaşarsanız:
1. Log dosyalarını kontrol edin
2. Environment variables'ları doğrulayın
3. Database bağlantısını test edin

---

**🎉 Başarılı deployment!** Projeniz artık canlıda!
