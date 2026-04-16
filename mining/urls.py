"""
URL configuration for the Silver Mining Database.
API routes return JsonResponse; /ui/* routes render HTML templates (data via fetch).
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.ui_login, name = 'login'),

    # ── Auth ──────────────────────────────────────────────────────────────────
    path('login/', views.login_view, name = 'login'),
    path('logout/', views.logout_view, name = 'logout'),
    path('register/', views.register_view, name = 'register'),

    # ── Shared ────────────────────────────────────────────────────────────────
    path('dashboard/', views.dashboard, name = 'dashboard'),

    # ── Investor ──────────────────────────────────────────────────────────────
    path('companies/', views.company_list, name = 'company_list'),
    path('companies/<str:ticker>/', views.company_detail, name = 'company_detail'),
    path('companies/<str:ticker>/favourite/', views.toggle_favourite, name = 'toggle_favourite'),
    path('favourites/', views.favourites_list, name = 'favourites'),

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

    # ── UI (HTML templates; JSON data loaded via fetch to routes above) ───────
    path('ui/login/', views.ui_login, name = 'ui_login'),
    path('ui/register/', views.ui_register, name = 'ui_register'),
    path('ui/dashboard/', views.ui_investor_dashboard, name = 'ui_investor_dashboard'),
    path('ui/companies/', views.ui_ranked_companies, name = 'ui_ranked_companies'),
    path('ui/companies/<str:ticker>/', views.ui_company_details, name = 'ui_company_details'),
    path('ui/favourites/', views.ui_favourites, name = 'ui_favourites'),
    path('ui/admin/', views.ui_admin_dashboard, name = 'ui_admin_dashboard'),
    path('ui/admin/companies/', views.ui_admin_companies, name = 'ui_admin_companies'),
    path('ui/admin/companies/add/', views.ui_admin_company_add, name = 'ui_admin_company_add'),
    path('ui/admin/companies/<str:ticker>/edit/', views.ui_admin_company_edit, name = 'ui_admin_company_edit'),
    path('ui/admin/investors/', views.ui_admin_investors, name = 'ui_admin_investors'),
    path('ui/admin/finmetrics/', views.ui_admin_finmetrics, name = 'ui_admin_finmetrics'),
    path('ui/admin/finmetrics/add/', views.ui_admin_finmetrics_add, name = 'ui_admin_finmetrics_add'),
    path('ui/admin/finmetrics/<str:ticker>/edit/', views.ui_admin_finmetrics_edit, name = 'ui_admin_finmetrics_edit'),
    path('ui/admin/stockprices/', views.ui_admin_stockprices, name = 'ui_admin_stockprices'),
    path('ui/admin/stockprices/add/', views.ui_admin_stockprice_add, name = 'ui_admin_stockprice_add'),
    path('ui/admin/stockprices/<str:ticker>/<str:date>/edit/', views.ui_admin_stockprice_edit, name = 'ui_admin_stockprice_edit'),
    path('ui/admin/production/', views.ui_admin_production, name = 'ui_admin_production'),
    path('ui/admin/production/add/', views.ui_admin_production_add, name = 'ui_admin_production_add'),
    path('ui/admin/production/<str:ticker>/<str:period>/edit/', views.ui_admin_production_edit, name = 'ui_admin_production_edit'),

    # DEV-ONLY: remove before submission
    path('dev-login/<str:role>/', views.dev_login, name = 'dev_login'),
]