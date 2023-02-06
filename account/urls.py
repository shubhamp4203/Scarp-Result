from re import template
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('home/', views.homepage, name="home"),
    path('home/scholar_ship_details', views.scholarshippage, name="scholarship"),
    path('ihome/', views.institutehomePage, name="Institutehome"),
    path('ghome/', views.governmenthomePage, name="Governmenthome"),
    path('password_reset_', views.password_reset_request, name="password_reset"),
    path('college_registration/', views.collegeregister, name="clgregister"),
    path('contact/', views.contactdetail, name="contact"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)