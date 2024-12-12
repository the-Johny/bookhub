from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin routes
    path('', include('bookapp.urls')),  # Bookapp routes for root paths
    path('admin-home/', include('adminapp.urls')),  # Matches your app name
    path('user-home/', include('userapp.urls')),  # Matches your app name
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



