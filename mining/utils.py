"""
Utility layer for the Silver Mining Database.

"""

from functools import wraps
from django.http import JsonResponse
from .models import Usertab, Finmetrics, Rankingreport


# ─────────────────────────────────────────────────────────────────────────────
# SESSION HELPERS
# ─────────────────────────────────────────────────────────────────────────────
# return the Usertab instance for the logged in user or None (looks up the user_id stored in the session on each call)
def get_current_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return Usertab.objects.get(pk = user_id)
    except Usertab.DoesNotExist:
        request.session.flush()
        return None

#write the user's ID and role into the session
def login_user(request, user):   
    request.session['user_id'] = user.user_id
    request.session['permission_level'] = user.permission_level

#destroy the entire session (logs the user out)
def logout_user(request):
    request.session.flush()


# ─────────────────────────────────────────────────────────────────────────────
# ROLE DECORATORS
# ─────────────────────────────────────────────────────────────────────────────
#redirect unauthenticated requests to login (Returns 401 JSON if the client expects JSON)
def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'error': 'Authentication required.'}, status = 401)
            return JsonResponse({'error': 'Please log in.'}, status = 401)
        return view_func(request, *args, **kwargs)
    return wrapper

#allow only Admin users (unauthenticated users get 401, investors get 403)
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return JsonResponse({'error': 'Authentication required.'}, status = 401)
        if request.session.get('permission_level') != 'Admin':
            return JsonResponse({'error': 'Admin access required.'}, status = 403)
        return view_func(request, *args, **kwargs)
    return wrapper

#allow only Investor users (unauthenticated users get 401, admins get 403)
def investor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return JsonResponse({'error': 'Authentication required.'}, status = 401)
        if request.session.get('permission_level') != 'Investor':
            return JsonResponse({'error': 'Investor access required.'}, status = 403)
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────────────────────────────────────

def compute_score(fm):
    """
    Compute a composite score (0-100) for a Finmetrics instance. Scoring puts most emphasis on low cost producers.

    Metric            Weight    Direction
    ─────────────────────────────────────
    AISC              35 pts    lower is better
    PEG ratio         25 pts    1.0 is ideal
    Debt to Equity    20 pts    lower is better
    EBITDA margin     20 pts    higher is better
    """
    score = 0.0

    #AISC score
    AISC_CEILING = 25.0
    aisc_val = float(fm.aisc)
    aisc_pts = max(0.0, (AISC_CEILING - aisc_val) / AISC_CEILING) * 35
    score += aisc_pts

    #PEG score
    peg_val = float(fm.peg)
    if 0 < peg_val <= 2.0:
        peg_pts = (1 - abs(peg_val - 1.0) / 2.0) * 25
    else:
        peg_pts = 0.0
    score += peg_pts

    #Debt to Equity score
    DE_CEILING = 2.0
    de_val = float(fm.debt_to_equity)
    de_pts = max(0.0, (DE_CEILING - de_val) / DE_CEILING) * 20
    score += de_pts

    #EBITDA margin score
    rev = float(fm.revenue)
    if rev > 0:
        margin = float(fm.ebitda) / rev
        margin = max(0.0, min(margin, 1.0))
        score += margin * 20
    return round(score, 2)


#recalculate scores for every company that has financial metrics and write the results back to RANKINGREPORT table (function called automatically after any insert or update on FIMETRICS table)
def rebuild_rankings():
    all_metrics = list(Finmetrics.objects.select_related('ticker').all())
    # Sort highest score first
    scored = sorted(
        [(fm, compute_score(fm)) for fm in all_metrics],
        key=lambda x: x[1],
        reverse=True,
    )

    for rank, (fm, score) in enumerate(scored, start=1):
        Rankingreport.objects.update_or_create(
            ticker=fm.ticker,
            defaults={'score': score, 'rank_position': rank},
        )