from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', core_views.robots_txt, name='robots_txt'),
    path('sitemap.xml', core_views.sitemap_xml, name='sitemap_xml'),
    path('', include('core.urls')),
    path('', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('', include('admin_panel.urls')),
    
    # Sentry Debug Route
    path('sentry-debug/', lambda r: 1 / 0),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
