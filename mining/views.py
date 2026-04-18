"""
Views for the Silver Mining Database.
All views return JsonResponse.
Session based auth stores user_id and permission_level after login.
"""

import json
from urllib.parse import unquote

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .models import (
    Usertab, Company, Favourite, Rankingreport,
    Finmetrics, Stockprice, Productiondata,
    Viewsdetails, Updatescompany, Updatesfinmetrics,
    Updatesstockprice, Updatesproductiondata,
)
from .form import (
    LoginForm, RegisterForm,
    CompanyForm, CompanyUpdateForm,
    FinmetricsForm, FinmetricsUpdateForm,
    StockpriceForm, StockpriceUpdateForm,
    ProductiondataForm, ProductiondataUpdateForm,
    CompanyFilterForm,
)
from .utils import (
    get_current_user, login_user, logout_user, rebuild_rankings,
    login_required, admin_required, investor_required,
)



# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

# Read incoming data from the request (works with both JSON and form encoded POST data)
def _body(request):
    ct = request.content_type or ''
    if 'application/json' in ct:
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return {}
    return request.POST.dict()

#Flatten form errors into a dict
def _form_errors(form):
    return {field: errs for field, errs in form.errors.items()}


# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
@require_http_methods(["POST"])
# POST { email, password }
# 200 { user_id, name, permission_level }
# 400 validation errors
# 401 bad credentials or pending approval
def login_view(request):
    form = LoginForm(_body(request))
    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status=400)

    email = form.cleaned_data['email']
    password = form.cleaned_data['password']

    try:
        user = Usertab.objects.get(user_email=email)
    except Usertab.DoesNotExist:
        return JsonResponse({'error': 'Invalid email or password.'}, status=401)

    if not user.check_password(password):
        return JsonResponse({'error': 'Invalid email or password.'}, status=401)

    if user.is_investor and not user.is_active:
        return JsonResponse({'error': 'Your account is pending admin approval.'}, status=401)

    login_user(request, user)

    return JsonResponse({
        'user_id':user.user_id,
        'name':f"{user.user_fname} {user.user_lname}",
        'permission_level':user.permission_level,
    })


@csrf_exempt
@require_http_methods(["POST"])
# POST 200 { message }
def logout_view(request):
    logout_user(request)
    return JsonResponse({'message': 'Logged out successfully.'})


@csrf_exempt
@require_http_methods(["POST"])
# POST { first_name, last_name, email, password, confirm_password }
# 201 { message } account starts inactive until admin approves
# 400 validation errors
def register_view(request):
    form = RegisterForm(_body(request))
    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status=400)

    user = Usertab(
        user_fname = form.cleaned_data['first_name'],
        user_lname = form.cleaned_data['last_name'],
        user_email = form.cleaned_data['email'],
        permission_level = Usertab.PermissionLevel.INVESTOR,
        is_active = False,
    )
    user.set_password(form.cleaned_data['password'])
    user.save()

    return JsonResponse({'message': 'Registration successful. Please wait for admin approval before logging in.'}, status = 201,)


# ══════════════════════════════════════════════════════════════════════════════
# SHARED
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@require_http_methods(["GET"])
# GET 200 { permission_level, redirect_to }
# tells the frontend whether to show the admin or investor interface
def dashboard(request):
    level = request.session.get('permission_level')
    return JsonResponse({'permission_level': level,'redirect_to': 'admin_dashboard' if level == 'Admin' else 'company_list'})


# ══════════════════════════════════════════════════════════════════════════════
# INVESTOR VIEWS
# ══════════════════════════════════════════════════════════════════════════════

@investor_required
@require_http_methods(["GET"])
# 
def company_list(request):
    form = CompanyFilterForm(request.GET)
    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status=400)

    cd = form.cleaned_data

    qs = (Rankingreport.objects.select_related('ticker', 'ticker__finmetrics').order_by('rank_position'))

    search = cd.get('search', '').strip()
    if search:
        qs = qs.filter(ticker__ticker__icontains=search) | \
             qs.filter(ticker__company_name__icontains=search)

    if cd.get('max_aisc') is not None:
        qs = qs.filter(ticker__finmetrics__aisc__lte=cd['max_aisc'])
    if cd.get('max_debt_equity') is not None:
        qs = qs.filter(ticker__finmetrics__debt_to_equity__lte=cd['max_debt_equity'])
    if cd.get('max_peg') is not None:
        qs = qs.filter(ticker__finmetrics__peg__lte=cd['max_peg'])

    results = []
    for rr in qs:
        fm = getattr(rr.ticker, 'finmetrics', None)
        results.append({
            'ticker':rr.ticker.ticker,
            'company_name':rr.ticker.company_name,
            'rank_position':rr.rank_position,
            'score':float(rr.score),
            'aisc':float(fm.aisc) if fm else None,
            'peg':float(fm.peg) if fm else None,
            'debt_to_equity': float(fm.debt_to_equity) if fm else None,
        })

    return JsonResponse({'companies': results})


@investor_required
@require_http_methods(["GET"])
#GET /companies/<ticker>/
#200 full company profile
#404 if ticker not found
def company_detail(request, ticker):
    try:
        company = Company.objects.get(pk=ticker)
    except Company.DoesNotExist:
        return JsonResponse({'error': f"Company '{ticker}' not found."}, status = 404)

    user = get_current_user(request)

    # Record the view — raw SQL because VIEWSDETAILS has no auto-id column
    try:
        with connection.cursor() as cur:
            cur.execute(
                "INSERT IGNORE INTO VIEWSDETAILS (InvestorID, Ticker) VALUES (%s, %s)",
                [user.user_id, company.ticker]
            )
    except Exception:
        pass

    # Ranking
    try:
        rr = Rankingreport.objects.get(ticker=company)
        ranking = {'score': float(rr.score), 'rank_position': rr.rank_position}
    except Rankingreport.DoesNotExist:
        ranking = None

    # Financial metrics
    try:
        fm = Finmetrics.objects.get(ticker=company)
        fin_metrics = {
            'aisc':float(fm.aisc),
            'peg':float(fm.peg),
            'total_debt':float(fm.total_debt),
            'debt_to_equity':float(fm.debt_to_equity),
            'revenue':float(fm.revenue),
            'ebitda':float(fm.ebitda),
        }
    except Finmetrics.DoesNotExist:
        fin_metrics = None

    # Stock prices most recent first
    stock_prices = [
        {
            'date_updated':str(sp.date_updated),
            'previous_open':float(sp.previous_open) if sp.previous_open else None,
            'previous_close':float(sp.previous_close) if sp.previous_close else None,
            'fifty_two_week_high':float(sp.fifty_two_week_high) if sp.fifty_two_week_high else None,
            'fifty_two_week_low':float(sp.fifty_two_week_low) if sp.fifty_two_week_low  else None,
        }
        for sp in Stockprice.objects.filter(ticker = company).order_by('-date_updated')
    ]

    # Production data most recent period first
    production = [
        {
            'period':pd.period,
            'silver_ounces_produced':float(pd.silver_ounces_produced) if pd.silver_ounces_produced else None,
            'notes':pd.notes,
        }
        for pd in Productiondata.objects.filter(ticker=company).order_by('-period')
    ]

    # Is this company favourited by the investor
    is_favourite = Favourite.objects.filter(investor=user, ticker=company).exists()

    return JsonResponse({
        'ticker':          company.ticker,
        'company_name':    company.company_name,
        'ranking':         ranking,
        'fin_metrics':     fin_metrics,
        'stock_prices':    stock_prices,
        'production_data': production,
        'is_favourite':    is_favourite,
    })


@csrf_exempt
@investor_required
@require_http_methods(["POST"])
#POST /companies/<ticker>/favourite/
#200 { is_favourite, message }
def toggle_favourite(request, ticker):
    try:
        company = Company.objects.get(pk = ticker)
    except Company.DoesNotExist:
        return JsonResponse({'error': f"Company '{ticker}' not found."}, status = 404)

    user = get_current_user(request)
    fav  = Favourite.objects.filter(investor = user, ticker = company)

    if fav.exists():
        fav.delete()
        return JsonResponse({
            'is_favourite': False,
            'message': f"{company.company_name} removed from favourites.",
        })
    else:
        Favourite.objects.create(
            investor = user,
            ticker = company,
            date_favourited = timezone.now().date(),
        )
        return JsonResponse({
            'is_favourite': True,
            'message': f"{company.company_name} added to favourites.",
        })


@investor_required
@require_http_methods(["GET"])
#GET /favourites/
#200 { favourites: [ { ticker, company_name, date_favourited } ] }
def favourites_list(request):
    user = get_current_user(request)
    # Raw SQL — FAVOURITE has no auto-id; queryset would SELECT FAVOURITE.id → error
    with connection.cursor() as cur:
        cur.execute(
            """SELECT f.Ticker, c.Company_Name, f.DateFavourited
               FROM FAVOURITE f
               JOIN COMPANY c ON c.Ticker = f.Ticker
               WHERE f.Investor_ID = %s
               ORDER BY f.DateFavourited DESC""",
            [user.user_id]
        )
        rows = cur.fetchall()
    return JsonResponse({
        'favourites': [
            {
                'ticker': row[0],
                'company_name': row[1],
                'date_favourited': str(row[2]),
            }
            for row in rows
        ]
    })


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@admin_required
@require_http_methods(["GET"])
def admin_dashboard(request):
    return JsonResponse({
        'total_companies': Company.objects.count(),
        'total_investors': Usertab.objects.filter(permission_level='Investor').count(),
        'pending_approvals': Usertab.objects.filter(permission_level='Investor', is_active=False).count(),
    })


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — COMPANY MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@admin_required
@require_http_methods(["GET"])
def admin_companies(request):
    companies = list(Company.objects.values('ticker', 'company_name').order_by('ticker'))
    return JsonResponse({'companies': companies})


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
#POST { ticker, company_name }
#201 { ticker, company_name }
def admin_company_add(request):
    form = CompanyForm(_body(request))
    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status = 400)

    admin   = get_current_user(request)
    company = form.save()
    with connection.cursor() as cur:
        cur.execute("INSERT IGNORE INTO UPDATESCOMPANY (AdminID, Ticker) VALUES (%s, %s)", [admin.user_id, company.ticker])

    return JsonResponse({'ticker': company.ticker, 'company_name': company.company_name}, status = 201,)


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
def admin_company_edit(request, ticker):
    """
    POST { company_name }
    200 { ticker, company_name }
    404 if not found
    """
    try:
        company = Company.objects.get(pk = ticker)
    except Company.DoesNotExist:
        return JsonResponse({'error': f"Company '{ticker}' not found."}, status = 404)

    form = CompanyUpdateForm(_body(request), instance=company)
    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status = 400)

    admin = get_current_user(request)
    company = form.save()
    with connection.cursor() as cur:
        cur.execute("INSERT IGNORE INTO UPDATESCOMPANY (AdminID, Ticker) VALUES (%s, %s)", [admin.user_id, company.ticker])

    return JsonResponse({'ticker': company.ticker, 'company_name': company.company_name})


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
def admin_company_delete(request, ticker):
    try:
        company = Company.objects.get(pk = ticker)
    except Company.DoesNotExist:
        return JsonResponse({'error': f"Company '{ticker}' not found."}, status = 404)

    company.delete()
    return JsonResponse({'message': f"Company '{ticker}' and all related data deleted."})


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — FINANCIAL METRICS
# ══════════════════════════════════════════════════════════════════════════════

@admin_required
@require_http_methods(["GET"])
def admin_finmetrics(request):
    finmetrics = list(Finmetrics.objects.values('ticker', 'aisc', 'peg', 'total_debt', 
                                                'debt_to_equity', 'revenue', 'ebitda').order_by('ticker'))
    return JsonResponse({'finmetrics': finmetrics})


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
#POST { ticker, aisc, peg, total_debt, debt_to_equity, revenue, abitda }
#201 { ticker, aisc, peg, total_debt, debt_to_equity, revenue, abitda }
def admin_finmetrics_add(request):
    form = FinmetricsForm(_body(request))
    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status = 400)

    admin   = get_current_user(request)
    finmetrics = form.save()
    with connection.cursor() as cur:
        cur.execute("INSERT IGNORE INTO UPDATESFINMETRICS (AdminID, Ticker) VALUES (%s, %s)", [admin.user_id, finmetrics.ticker_id])

    return JsonResponse({'ticker': finmetrics.ticker_id, 'aisc': float(finmetrics.aisc), 
                         'peg': float(finmetrics.peg), 'total_debt': float(finmetrics.total_debt),
                         'debt_to_equity': float(finmetrics.debt_to_equity), 
                         'revenue': float(finmetrics.revenue), 'ebitda': float(finmetrics.ebitda)}, status = 201,)


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
def admin_finmetrics_edit(request, ticker):
    try:
        finmetrics = Finmetrics.objects.get(pk = ticker)
    except Finmetrics.DoesNotExist:
        return JsonResponse({'error': f"Company '{ticker}' not found."}, status = 404)

    form = FinmetricsUpdateForm(_body(request), instance=finmetrics)
    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status = 400)

    admin = get_current_user(request)
    finmetrics = form.save()
    with connection.cursor() as cur:
        cur.execute("INSERT IGNORE INTO UPDATESFINMETRICS (AdminID, Ticker) VALUES (%s, %s)", [admin.user_id, finmetrics.ticker_id])

    return JsonResponse({'ticker': finmetrics.ticker_id, 'aisc': float(finmetrics.aisc), 
                         'peg': float(finmetrics.peg), 'total_debt': float(finmetrics.total_debt),
                         'debt_to_equity': float(finmetrics.debt_to_equity), 
                         'revenue': float(finmetrics.revenue), 'ebitda': float(finmetrics.ebitda)})


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
def admin_finmetrics_delete(request, ticker):
    try:
        finmetrics = Finmetrics.objects.get(pk = ticker)
    except Finmetrics.DoesNotExist:
        return JsonResponse({'error': f"Company '{ticker}' not found."}, status = 404)

    finmetrics.delete()
    return JsonResponse({'message': f"Company '{ticker}' financial metrics deleted."})


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — STOCK PRICES
# ══════════════════════════════════════════════════════════════════════════════

@admin_required
@require_http_methods(["GET"])
def admin_stockprices(request):
    stockprices = list(Stockprice.objects.values('ticker', 'date_updated','previous_open', 'previous_close', 
                                                 'fifty_two_week_high', 'fifty_two_week_low').order_by('ticker'))
    return JsonResponse({'stockprices': stockprices})


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
#POST { ticker, date_updated, previous_open, previous_close, fifty_two_week_high, fifty_two_week_low }
#201 { ticker, date_updated, previous_open, previous_close, fifty_two_week_high, fifty_two_week_low }
def admin_stockprice_add(request):
    form = StockpriceForm(_body(request))
    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status = 400)

    admin   = get_current_user(request)
    stockprice = form.save(commit=False)
    stockprice.save(force_insert=True)   # composite PK — always INSERT
    with connection.cursor() as cur:
        cur.execute("INSERT IGNORE INTO UPDATESSTOCKPRICE (AdminID, Ticker, Date_Updated) VALUES (%s, %s, %s)",
                    [admin.user_id, stockprice.ticker_id, stockprice.date_updated])

    return JsonResponse({'ticker': stockprice.ticker_id, 'date_updated': str(stockprice.date_updated), 
                         'previous_open': str(stockprice.previous_open or ''),
                         'previous_close': str(stockprice.previous_close or ''),
                         'fifty_two_week_high': str(stockprice.fifty_two_week_high or ''),
                         'fifty_two_week_low': str(stockprice.fifty_two_week_low or '')}, status = 201,)


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
def admin_stockprice_edit(request, ticker, date):
    d = parse_date(date)
    if d is None:
        return JsonResponse({'error': 'Invalid date.'}, status=400)
    try:
        stockprice = Stockprice.objects.get(ticker_id=ticker, date_updated=d)
    except Stockprice.DoesNotExist:
        return JsonResponse({'error': f"No stock price for '{ticker}' on {date}."}, status=404)

    form = StockpriceUpdateForm(_body(request), instance=stockprice)
    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status = 400)

    admin = get_current_user(request)
    cd = form.cleaned_data
    # Raw SQL UPDATE — Django ORM cannot reliably UPDATE composite-PK tables
    with connection.cursor() as cur:
        cur.execute(
            """UPDATE STOCKPRICE
               SET PreviousOpen=%s, PreviousClose=%s, FiftyTwoWeekHigh=%s, FiftyTwoWeekLow=%s
               WHERE Ticker=%s AND Date_Updated=%s""",
            [cd['previous_open'], cd['previous_close'], cd['fifty_two_week_high'], cd['fifty_two_week_low'],
             ticker, d]
        )
        cur.execute("INSERT IGNORE INTO UPDATESSTOCKPRICE (AdminID, Ticker, Date_Updated) VALUES (%s, %s, %s)",
                    [admin.user_id, ticker, d])

    return JsonResponse({'ticker': ticker, 'date_updated': str(d),
                         'previous_open': str(cd['previous_open'] or ''),
                         'previous_close': str(cd['previous_close'] or ''),
                         'fifty_two_week_high': str(cd['fifty_two_week_high'] or ''),
                         'fifty_two_week_low': str(cd['fifty_two_week_low'] or '')})


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
def admin_stockprice_delete(request, ticker, date):
    d = parse_date(date)
    if d is None:
        return JsonResponse({'error': 'Invalid date.'}, status=400)
    try:
        stockprice = Stockprice.objects.get(ticker_id=ticker, date_updated=d)
    except Stockprice.DoesNotExist:
        return JsonResponse({'error': f"No stock price for '{ticker}' on {date}."}, status=404)

    stockprice.delete()
    return JsonResponse({'message': f"Stock price for '{ticker}' on {date} deleted."})


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — PRODUCTION DATA
# ══════════════════════════════════════════════════════════════════════════════

@admin_required
@require_http_methods(["GET"])
def admin_production(request):
    productiondata = list(Productiondata.objects.values('ticker', 'period', 'silver_ounces_produced', 
                                                        'notes').order_by('ticker'))
    return JsonResponse({'productiondata': productiondata})


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
#POST { ticker, period, silver_ounces_produced, notes }
#201 { ticker, period, silver_ounces_produced, notes }
def admin_production_add(request):
    form = ProductiondataForm(_body(request))
    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status = 400)

    admin   = get_current_user(request)
    productiondata = form.save(commit=False)
    productiondata.save(force_insert=True)   # composite PK — always INSERT
    with connection.cursor() as cur:
        cur.execute("INSERT IGNORE INTO UPDATESPRODUCTIONDATA (AdminID, Ticker, Period) VALUES (%s, %s, %s)",
                    [admin.user_id, productiondata.ticker_id, productiondata.period])

    return JsonResponse({'ticker': productiondata.ticker_id, 'period': productiondata.period, 
                         'silver_ounces_produced': str(productiondata.silver_ounces_produced or ''), 
                         'notes': productiondata.notes or ''}, status = 201,)


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
def admin_production_edit(request, ticker, period):
    period = unquote(period)
    try:
        productiondata = Productiondata.objects.get(ticker_id=ticker, period=period)
    except Productiondata.DoesNotExist:
        return JsonResponse({'error': f"No production row for '{ticker}' / '{period}'."}, status = 404)

    form = ProductiondataUpdateForm(_body(request), instance=productiondata)
    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status = 400)

    admin = get_current_user(request)
    cd = form.cleaned_data
    # Raw SQL UPDATE — Django ORM cannot reliably UPDATE composite-PK tables
    with connection.cursor() as cur:
        cur.execute(
            "UPDATE PRODUCTIONDATA SET SilverOuncesProduced=%s, Notes=%s WHERE Ticker=%s AND Period=%s",
            [cd.get('silver_ounces_produced'), cd.get('notes', ''), ticker, period]
        )
        cur.execute("INSERT IGNORE INTO UPDATESPRODUCTIONDATA (AdminID, Ticker, Period) VALUES (%s, %s, %s)",
                    [admin.user_id, ticker, period])

    return JsonResponse({'ticker': ticker, 'period': period, 
                         'silver_ounces_produced': str(cd.get('silver_ounces_produced') or ''), 
                         'notes': cd.get('notes', '') or ''})


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
def admin_production_delete(request, ticker, period):
    period = unquote(period)
    try:
        productiondata = Productiondata.objects.get(ticker_id=ticker, period=period)
    except Productiondata.DoesNotExist:
        return JsonResponse({'error': f"No production row for '{ticker}' / '{period}'."}, status = 404)

    productiondata.delete()
    return JsonResponse({'message': f"Production row for '{ticker}' / '{period}' deleted."})


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — INVESTOR MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@admin_required
@require_http_methods(["GET"])
# GET 200 { investors: [ { user_id, first_name, last_name, email, permission_level, is_active } ] }
def admin_investors(request):
    investors = (
        Usertab.objects.filter(permission_level=Usertab.PermissionLevel.INVESTOR)
        .order_by('user_id')
    )
    return JsonResponse({
        'investors': [
            {
                'user_id': u.user_id,
                'first_name': u.user_fname,
                'last_name': u.user_lname,
                'email': u.user_email,
                'permission_level': u.permission_level,
                'is_active': u.is_active,
            }
            for u in investors
        ]
    })


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
# POST — approve pending investor (sets is_active True)
# 200 { message, user_id }
# 404 user not found
# 400 if target is not an investor
def admin_investor_approve(request, user_id):
    try:
        user = Usertab.objects.get(pk=user_id)
    except Usertab.DoesNotExist:
        return JsonResponse({'error': f"User with id {user_id} not found."}, status=404)

    if not user.is_investor:
        return JsonResponse({'error': 'Target user is not an investor.'}, status=400)

    user.is_active = True
    user.save(update_fields=['is_active'])

    return JsonResponse({
        'message': 'Investor approved successfully.',
        'user_id': user.user_id,
    })


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
# POST — deactivate investor account
# 200 { message, user_id }
# 404 user not found
# 400 if target is not an investor
def admin_investor_deactivate(request, user_id):
    try:
        user = Usertab.objects.get(pk=user_id)
    except Usertab.DoesNotExist:
        return JsonResponse({'error': f"User with id {user_id} not found."}, status=404)

    if not user.is_investor:
        return JsonResponse({'error': 'Target user is not an investor.'}, status=400)

    user.is_active = False
    user.save(update_fields=['is_active'])

    return JsonResponse({
        'message': 'Investor deactivated successfully.',
        'user_id': user.user_id,
    })


@csrf_exempt
@admin_required
@require_http_methods(["POST"])
# POST — delete investor user record
# 200 { message, user_id }
# 404 user not found
# 400 if target is not an investor
def admin_investor_delete(request, user_id):
    try:
        user = Usertab.objects.get(pk=user_id)
    except Usertab.DoesNotExist:
        return JsonResponse({'error': f"User with id {user_id} not found."}, status=404)

    if not user.is_investor:
        return JsonResponse({'error': 'Target user is not an investor.'}, status=400)

    uid = user.user_id
    user.delete()

    return JsonResponse({
        'message': 'Investor deleted successfully.',
        'user_id': uid,
    })


# ══════════════════════════════════════════════════════════════════════════════
# HTML UI — thin template shells; data loaded via fetch to JSON routes above.
# ══════════════════════════════════════════════════════════════════════════════

def _render_ui(request, template, page_title, nav_mode, nav_active='', extra=None):
    ctx = {
        'page_title': page_title,
        'nav_mode': nav_mode,
        'nav_active': nav_active,
    }
    if extra:
        ctx.update(extra)
    return render(request, template, ctx)


def ui_login(request):
    extra = {}
    if request.GET.get('registered') == '1':
        extra['auth_banner'] = {
            'type': 'success',
            'text': 'Account created. Log in once an admin has approved your account.',
        }
    return _render_ui(request, 'mining/ui_login.html', 'Log in', 'auth', 'login', extra)


def ui_register(request):
    return _render_ui(request, 'mining/ui_register.html', 'Register', 'auth', 'register')


def ui_investor_dashboard(request):
    return _render_ui(request, 'mining/investor_dashboard.html', 'Investor dashboard', 'investor', 'dashboard')


def ui_ranked_companies(request):
    return _render_ui(request, 'mining/ranked_companies.html', 'Ranked companies', 'investor', 'companies')


def ui_company_details(request, ticker):
    return _render_ui(
        request,
        'mining/company_details.html',
        'Company details',
        'investor',
        'companies',
        {'ticker': ticker},
    )


def ui_favourites(request):
    return _render_ui(request, 'mining/favourites.html', 'Favourites', 'investor', 'favourites')


def ui_admin_dashboard(request):
    return _render_ui(request, 'mining/admin_dashboard.html', 'Admin dashboard', 'admin', 'dashboard')


def ui_admin_companies(request):
    return _render_ui(request, 'mining/admin_companies.html', 'Companies', 'admin', 'companies')


def ui_admin_company_add(request):
    return _render_ui(request, 'mining/add_company.html', 'Add company', 'admin', 'companies')


def ui_admin_company_edit(request, ticker):
    return _render_ui(
        request,
        'mining/edit_company.html',
        'Edit company',
        'admin',
        'companies',
        {'ticker': ticker},
    )


def ui_admin_investors(request):
    return _render_ui(request, 'mining/manage_investors.html', 'Manage investors', 'admin', 'investors')


def ui_admin_finmetrics(request):
    return _render_ui(request, 'mining/financial_metrics.html', 'Financial metrics', 'admin', 'finmetrics')


def ui_admin_finmetrics_add(request):
    return _render_ui(request, 'mining/add_finmetrics.html', 'Add financial metrics', 'admin', 'finmetrics')


def ui_admin_finmetrics_edit(request, ticker):
    return _render_ui(
        request,
        'mining/edit_finmetrics.html',
        'Edit financial metrics',
        'admin',
        'finmetrics',
        {'ticker': ticker},
    )


def ui_admin_stockprices(request):
    return _render_ui(request, 'mining/stock_prices.html', 'Stock prices', 'admin', 'stockprices')


def ui_admin_stockprice_add(request):
    return _render_ui(request, 'mining/add_stockprice.html', 'Add stock price', 'admin', 'stockprices')


def ui_admin_stockprice_edit(request, ticker, date):
    return _render_ui(
        request,
        'mining/edit_stockprice.html',
        'Edit stock price',
        'admin',
        'stockprices',
        {'ticker': ticker, 'quote_date': date},
    )


def ui_admin_production(request):
    return _render_ui(request, 'mining/production_data.html', 'Production data', 'admin', 'production')


def ui_admin_production_add(request):
    return _render_ui(request, 'mining/add_production.html', 'Add production record', 'admin', 'production')


def ui_admin_production_edit(request, ticker, period):
    return _render_ui(
        request,
        'mining/edit_production.html',
        'Edit production record',
        'admin',
        'production',
        {'ticker': ticker, 'period': unquote(period)},
    )
