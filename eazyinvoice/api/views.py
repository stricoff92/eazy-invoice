
from io import BytesIO

from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http.response import HttpResponseBadRequest, FileResponse
from django.views.decorators.http import require_GET, require_http_methods
from django.utils import timezone

from api.models import HoursEntry, Organization, Invoice
from api.login_form import LoginForm
from api.services import invoice_lib
from eazyinvoice.secrets import get_auth_code


@require_GET
def landing_page(request):
    if not request.user.is_authenticated:
        return redirect("page-login")
    return redirect("page-orgs")


@require_http_methods(["GET", "POST"])
def login_user(request):
    if request.method.upper() == "GET":
        if request.user.is_authenticated:
            return redirect("page-orgs")
        return render(request, "login.html")

    elif request.method.upper() == "POST":
        error_context = {"error": "invalid username/password"}
        form = LoginForm(request.POST)
        # Check form is valid
        if not form.is_valid():
            return render(
                request,
                "login.html",
                error_context,
            )

        # Check auth code
        if str(form.cleaned_data['authcode']) != str(get_auth_code()):
            return render(
                request,
                "login.html",
                error_context,
            )

        # Check username/password
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'])

        if user is not None:
            login(request, user)
            return redirect("page-orgs")
        else:
            return render(
                request,
                "login.html",
                error_context,
            )
    else:
        return HttpResponseBadRequest()


@require_GET
@login_required
def logout_user(requst):
    logout(requst)
    return redirect("page-login")


@require_GET
@login_required
def orgs(request):
    orglist = (Organization
        .objects
        .filter(user=request.user)
        .order_by('short_name')
        .values("id", "legal_name",)
    )
    if orglist.count() == 1:
        return redirect("page-org", orgId=orglist.first()['id'])
    return render(
        request,
        "orgs.html",
        {'orgs': orglist, 'breadcrumbs': [{'value':'org list'}]}
    )


@require_GET
@login_required
def org(request, orgId: str):
    org = get_object_or_404(Organization, id=orgId, user=request.user)
    rates = org.hourlyrate_set.order_by("-rate").values("id", "rate")
    entries_to_invoice = (HoursEntry
        .objects
        .filter(rate__organization=org, invoice__isnull=True)
        .order_by('-created_at')
        .values("id", "date", "quantity", "description", "rate__rate")
    )
    invoices = invoice_lib.get_created_invoices_data(org)

    return render(
        request,
        "org.html",
        {
            "org": org,
            "rates": rates,
            "invoices": invoices,
            "today": timezone.now().date().isoformat(),
            "entries_to_invoice": entries_to_invoice,
            'breadcrumbs': [
                {'value':'org list', 'href':reverse("page-orgs")},
                {'value': org.short_name}
            ]
        },
    )


@require_GET
@login_required
def download_invoice(request, orgId: str, invoiceId: str):
    org = get_object_or_404(Organization, id=orgId, user=request.user)
    invoice = get_object_or_404(
        Invoice,
        organization=org,
        id=invoiceId,
    )
    invoiceFile = invoice_lib.create_invoice_pdf(invoice)
    return FileResponse(
        BytesIO(invoiceFile),
        as_attachment=True,
        filename=invoice.download_file_name,
    )
