from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from .models import ExchangeRequest
from .forms import ExchangeForm
from .constants import WALLETS, EXCHANGE_RATE, MIN_AMOUNT, MAX_AMOUNT
import json


def home(request):
    wallets = [{'key': k, **v} for k, v in WALLETS.items()]
    context = {
        'wallets': wallets,
        'exchange_rate': EXCHANGE_RATE,
        'min_amount': MIN_AMOUNT,
        'max_amount': MAX_AMOUNT,
    }
    return render(request, 'exchange/home.html', context)


def wallet_detail(request, wallet_key):
    if wallet_key not in WALLETS:
        messages.error(request, 'Wallet not found.')
        return redirect('home')

    wallet = {'key': wallet_key, **WALLETS[wallet_key]}
    form = ExchangeForm()

    if request.method == 'POST':
        form = ExchangeForm(request.POST, request.FILES)
        if form.is_valid():
            exchange = form.save(commit=False)
            exchange.wallet = wallet_key
            exchange.save()
            return redirect('exchange_success', ref=str(exchange.reference_id))

    context = {
        'wallet': wallet,
        'form': form,
        'exchange_rate': EXCHANGE_RATE,
        'min_amount': MIN_AMOUNT,
        'max_amount': MAX_AMOUNT,
    }
    return render(request, 'exchange/wallet_detail.html', context)


def exchange_success(request, ref):
    exchange = get_object_or_404(ExchangeRequest, reference_id=ref)
    return render(request, 'exchange/success.html', {'exchange': exchange})


def track_order(request):
    exchange = None
    ref = ''
    if request.method == 'POST':
        ref = request.POST.get('reference', '').strip()
        try:
            exchange = ExchangeRequest.objects.get(reference_id=ref)
        except (ExchangeRequest.DoesNotExist, Exception):
            messages.error(request, 'No order found with this reference ID.')
    return render(request, 'exchange/track.html', {'exchange': exchange, 'ref': ref})


# ── Language switcher ─────────────────────────────────────────────────────────

def set_language(request):
    lang = request.POST.get('language', 'en')
    if lang in ('en', 'fr'):
        request.session['lang'] = lang
    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)


# ── Dashboard views ────────────────────────────────────────────────────────────

def dashboard_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'dashboard/login.html')


def dashboard_logout(request):
    logout(request)
    return redirect('home')


@login_required(login_url='/dashboard/login/')
def dashboard(request):
    requests_qs = ExchangeRequest.objects.all()
    stats = {
        'total': requests_qs.count(),
        'pending': requests_qs.filter(status='pending').count(),
        'processing': requests_qs.filter(status='processing').count(),
        'completed': requests_qs.filter(status='completed').count(),
        'rejected': requests_qs.filter(status='rejected').count(),
    }
    wallet_stats = (
        requests_qs.values('wallet')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    recent = requests_qs[:10]
    context = {
        'stats': stats,
        'wallet_stats': wallet_stats,
        'recent': recent,
        'wallets': WALLETS,
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required(login_url='/dashboard/login/')
def dashboard_requests(request):
    qs = ExchangeRequest.objects.all()
    status_filter = request.GET.get('status', '')
    wallet_filter = request.GET.get('wallet', '')
    search = request.GET.get('q', '')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if wallet_filter:
        qs = qs.filter(wallet=wallet_filter)
    if search:
        qs = qs.filter(
            Q(moneygo_wallet__icontains=search) |
            Q(email__icontains=search) |
            Q(whatsapp_number__icontains=search)
        )

    context = {
        'requests': qs,
        'wallets': WALLETS,
        'status_filter': status_filter,
        'wallet_filter': wallet_filter,
        'search': search,
        'status_choices': ExchangeRequest.STATUS_CHOICES,
    }
    return render(request, 'dashboard/requests.html', context)


@login_required(login_url='/dashboard/login/')
def dashboard_request_detail(request, pk):
    exchange = get_object_or_404(ExchangeRequest, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        admin_note = request.POST.get('admin_note', '')
        if new_status in dict(ExchangeRequest.STATUS_CHOICES):
            exchange.status = new_status
            exchange.admin_note = admin_note
            exchange.save()
            messages.success(request, f'Request updated to {exchange.get_status_display()}.')
            return redirect('dashboard_request_detail', pk=pk)
    context = {
        'exchange': exchange,
        'wallets': WALLETS,
        'status_choices': ExchangeRequest.STATUS_CHOICES,
    }
    return render(request, 'dashboard/request_detail.html', context)


@login_required(login_url='/dashboard/login/')
@require_POST
def dashboard_update_status(request, pk):
    exchange = get_object_or_404(ExchangeRequest, pk=pk)
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        if new_status in dict(ExchangeRequest.STATUS_CHOICES):
            exchange.status = new_status
            exchange.save()
            return JsonResponse({'success': True, 'status': exchange.get_status_display()})
    except Exception:
        pass
    return JsonResponse({'success': False}, status=400)
