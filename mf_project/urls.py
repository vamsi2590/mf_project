from django.contrib import admin
from django.urls import path, include
from django.conf.urls import handler404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mf_app.urls')),  # Main entry
]

handler404 = 'mf_app.views.error_404'
