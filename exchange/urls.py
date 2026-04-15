from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('exchange/<str:wallet_key>/', views.wallet_detail, name='wallet_detail'),
    path('exchange/success/<uuid:ref>/', views.exchange_success, name='exchange_success'),
    path('track/', views.track_order, name='track_order'),

    # Language
    path('set-language/', views.set_language, name='set_language'),

    # Dashboard
    path('dashboard/login/', views.dashboard_login, name='dashboard_login'),
    path('dashboard/logout/', views.dashboard_logout, name='dashboard_logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/requests/', views.dashboard_requests, name='dashboard_requests'),
    path('dashboard/requests/<int:pk>/', views.dashboard_request_detail, name='dashboard_request_detail'),
    path('dashboard/requests/<int:pk>/status/', views.dashboard_update_status, name='dashboard_update_status'),
]
