from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [

    path('', views.index, name='index'),
    path('signup/', views.signup_view, name='signup_view'),
    path('login/', views.login_view, name='login_view'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about, name='about'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('feature/', views.feature, name='feature'),
    path('offer/', views.offer, name='offer'),
    path('service/', views.service, name='service'),
    path('team/', views.team, name='team'),
    path('testimonial/', views.testimonial, name='testimonial'),
    path('404/', views.error_404, name='error_404'),
    path('purchase-tracker/', views.purchase_tracker, name='purchase_tracker'),

    


]
