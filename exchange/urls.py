from django.urls import path
from . import views

urlpatterns = [
    # ── Pages publiques ──────────────────────────────────────────────────────
    path('', views.home, name='home'),
    path('exchange/<str:wallet_key>/', views.wallet_detail, name='wallet_detail'),
    path('exchange/success/<uuid:ref>/', views.exchange_success, name='exchange_success'),
    path('track/', views.track_order, name='track_order'),
    path('set-language/', views.set_language, name='set_language'),

    # ── Authentification utilisateur ─────────────────────────────────────────
    path('inscription/', views.user_register, name='user_register'),
    path('connexion/', views.user_login, name='user_login'),
    path('deconnexion/', views.user_logout, name='user_logout'),

    # ── Espace utilisateur ───────────────────────────────────────────────────
    path('mon-compte/', views.user_dashboard, name='user_dashboard'),
    path('mon-compte/demandes/', views.user_requests, name='user_requests'),
    path('mon-compte/nouvelle-demande/', views.user_new_request, name='user_new_request'),
    path('mon-compte/demandes/<int:pk>/', views.user_request_detail, name='user_request_detail'),

    # ── Dashboard admin ──────────────────────────────────────────────────────
    path('dashboard/login/', views.dashboard_login, name='dashboard_login'),
    path('dashboard/logout/', views.dashboard_logout, name='dashboard_logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/requests/', views.dashboard_requests, name='dashboard_requests'),
    path('dashboard/requests/<int:pk>/', views.dashboard_request_detail, name='dashboard_request_detail'),
    path('dashboard/requests/<int:pk>/status/', views.dashboard_update_status, name='dashboard_update_status'),
    path('dashboard/history/sent/', views.dashboard_history_sent, name='dashboard_history_sent'),
    path('dashboard/history/rejected/', views.dashboard_history_rejected, name='dashboard_history_rejected'),
]
