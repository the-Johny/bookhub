from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from bookhub import settings

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin routes
    path('', include('bookapp.urls')),  # Bookapp routes for root paths
    path('admin-app/', include('AdminApp.urls')),  # Matches your app name
    path('user-app/', include('UserApp.urls')),  # Matches your app name
]

if settings.DEBUG:  # Serve media files only during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
