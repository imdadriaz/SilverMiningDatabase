"""
URL configuration for the Silver Mining Database.
Every URL maps to a view that returns JsonResponse.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name = 'home'),

    # ── Auth ──────────────────────────────────────────────────────────────────
    path('login/', views.login, name = 'login'),
    path('logout/', views.logout_view, name = 'logout'),
    path('register/', views.register, name = 'register'),
    path('register/message/', views.register_view, name = 'register_message'),


    # ── Shared ────────────────────────────────────────────────────────────────
    path('dashboard/', views.dashboard, name = 'dashboard'),

    # ── Investor ──────────────────────────────────────────────────────────────
    path('companies/', views.company_list, name = 'company_list'),
    path('companies/<str:ticker>/', views.company_detail, name = 'company_detail'),
    path('companies/<str:ticker>/favourite/', views.toggle_favourite, name = 'toggle_favourite'),
    path('favourites/', views.favourites, name = 'favourites'),

    # ── Admin — dashboard ─────────────────────────────────────────────────────
    path('admin/', views.admin_dashboard, name = 'admin_dashboard'),

    # ── Admin — companies ─────────────────────────────────────────────────────
    path('admin/companies/', views.admin_companies, name = 'admin_companies'),
    path('admin/companies/add/', views.admin_company_add, name = 'admin_company_add'),
    path('admin/companies/<str:ticker>/edit/', views.admin_company_edit, name = 'admin_company_edit'),
    path('admin/companies/<str:ticker>/delete/', views.admin_company_delete, name = 'admin_company_delete'),

    # ── Admin — financial metrics ─────────────────────────────────────────────
    path('admin/finmetrics/', views.admin_finmetrics, name = 'admin_finmetrics'),
    path('admin/finmetrics/add/', views.admin_finmetrics_add, name = 'admin_finmetrics_add'),
    path('admin/finmetrics/<str:ticker>/edit/', views.admin_finmetrics_edit, name = 'admin_finmetrics_edit'),
    path('admin/finmetrics/<str:ticker>/delete/', views.admin_finmetrics_delete, name = 'admin_finmetrics_delete'),

    # ── Admin — stock prices ──────────────────────────────────────────────────
    path('admin/stockprices/', views.admin_stockprices, name = 'admin_stockprices'),
    path('admin/stockprices/add/', views.admin_stockprice_add, name = 'admin_stockprice_add'),
    path('admin/stockprices/<str:ticker>/<str:date>/edit/', views.admin_stockprice_edit, name = 'admin_stockprice_edit'),
    path('admin/stockprices/<str:ticker>/<str:date>/delete/', views.admin_stockprice_delete, name = 'admin_stockprice_delete'),

    # ── Admin — production data ───────────────────────────────────────────────
    path('admin/production/', views.admin_production, name = 'admin_production'),
    path('admin/production/add/', views.admin_production_add, name = 'admin_production_add'),
    path('admin/production/<str:ticker>/<str:period>/edit/', views.admin_production_edit, name = 'admin_production_edit'),
    path('admin/production/<str:ticker>/<str:period>/delete/', views.admin_production_delete, name = 'admin_production_delete'),

    # ── Admin — investor management ───────────────────────────────────────────
    path('admin/investors/', views.admin_investors, name = 'admin_investors'),
    path('admin/investors/<int:user_id>/approve/', views.admin_investor_approve, name = 'admin_investor_approve'),
    path('admin/investors/<int:user_id>/deactivate/', views.admin_investor_deactivate, name = 'admin_investor_deactivate'),
    path('admin/investors/<int:user_id>/delete/', views.admin_investor_delete, name = 'admin_investor_delete'),
]