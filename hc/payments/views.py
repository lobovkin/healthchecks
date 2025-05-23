from __future__ import annotations

from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from hc.accounts.http import AuthenticatedHttpRequest
from hc.front.views import _get_project_for_user
from hc.payments.models import Subscription


def pricing(request: HttpRequest, code: str | None = None) -> HttpResponse:
    project = None
    if code:
        if not request.user.is_authenticated:
            raise Http404()

        # Convert string to UUID before passing to _get_project_for_user
        project, rw = _get_project_for_user(request, UUID(code))
        if project.owner != request.user:
            ctx = {"page": "pricing", "project": project}
            return render(request, "payments/pricing_not_owner.html", ctx)

    sub = None
    if request.user.is_authenticated:
        # Don't use Subscription.objects.for_user method here, so a
        # subscription object is not created just by viewing a page.
        sub = Subscription.objects.filter(user_id=request.user.id).first()

    ctx = {"page": "pricing", "project": project, "sub": sub}
    return render(request, "payments/pricing.html", ctx)

@login_required
def billing(request: AuthenticatedHttpRequest) -> HttpResponse:
    # Don't use Subscription.objects.for_user method here, so a
    # subscription object is not created just by viewing a page.
    user_id = request.user.id
    if user_id is not None:
        sub = Subscription.objects.filter(user_id=user_id).first()
        if sub is None:
            # Since we're in a login_required view, we know this is an authenticated user
            sub = Subscription(user=request.user)
    else:
        sub = None

    ctx = {
        "page": "billing",
        "profile": request.profile,
        "sub": sub,
        "set_plan_status": "default",
        "address_status": "default",
        "payment_method_status": "default",
    }

    if "set_plan_status" in request.session:
        ctx["set_plan_status"] = request.session.pop("set_plan_status")

    if "address_status" in request.session:
        ctx["address_status"] = request.session.pop("address_status")

    if "payment_method_status" in request.session:
        ctx["payment_method_status"] = request.session.pop("payment_method_status")

    return render(request, "accounts/billing.html", ctx)
