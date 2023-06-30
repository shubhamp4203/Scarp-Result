from re import template
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('', views.homepage, name="home"),
    path('ahome/', views.adminpage, name="Adminhome"),
    path('ahome/approved', views.approvedreq, name="approved"),
    path('login/', views.loginPage, name="login"),
    path('ScrappedResultAdmin/', views.adminlogin, name="adminlogin"),
    path('logout/', views.logoutUser, name="logout"),
    path('home/scholar_ship_details', views.scholarshippage, name="scholarship"),
    path('ihome/', views.institutehomePage, name="Institutehome"),
    path('ghome/', views.governmenthomePage, name="Governmenthome"),
    path('password_reset_', views.password_reset_request, name="password_reset"),
    path('college_registration/', views.collegeregister, name="clgregister"),
    path('contact/', views.contactdetail, name="contact"),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('ahome/<int:clg_id>/', views.clg_letter, name='clg_id'),
    path('ahome/accept/<str:clg_name>/', views.accept, name="accept"),
    path('ahome/reject/<str:clg_name>/', views.reject, name="reject"),
    path('generate_pdf/<int:student>/', views.generate_pdf, name='generate_pdf'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)