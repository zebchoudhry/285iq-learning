"""
Stripe Checkout subscription billing: create session, webhook, status, success/cancel pages.
"""
from datetime import datetime, timezone as dt_timezone

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.contrib.auth import get_user_model

User = get_user_model()


def _stripe_configured():
    return bool(getattr(settings, "STRIPE_SECRET_KEY", "") or "")


def _apply_subscription_from_stripe_subscription(student, sub, price_id=None):
    """Update Student from Stripe Subscription object (dict)."""
    customer_id = sub.get("customer")
    if isinstance(customer_id, dict):
        customer_id = customer_id.get("id")
    student.stripe_customer_id = customer_id or student.stripe_customer_id
    student.stripe_subscription_id = sub.get("id") or student.stripe_subscription_id

    cpe = sub.get("current_period_end")
    if cpe:
        student.subscription_expires_at = datetime.fromtimestamp(
            int(cpe), tz=dt_timezone.utc
        )

    items = (sub.get("items") or {}).get("data") or []
    if items:
        price_id = items[0].get("price", {}).get("id") or price_id

    monthly_pid = getattr(settings, "STRIPE_MONTHLY_PRICE_ID", "") or ""
    annual_pid = getattr(settings, "STRIPE_ANNUAL_PRICE_ID", "") or ""

    st = sub.get("status") or ""
    if st in ("canceled", "unpaid", "incomplete_expired"):
        student.subscription_status = "cancelled"
    elif st in ("active", "trialing", "past_due"):
        if price_id == monthly_pid:
            student.subscription_status = "pro_monthly"
        elif price_id == annual_pid:
            student.subscription_status = "pro_annual"
        else:
            if student.subscription_status not in ("pro_monthly", "pro_annual"):
                student.subscription_status = "pro_monthly"
    student.save(
        update_fields=[
            "stripe_customer_id",
            "stripe_subscription_id",
            "subscription_expires_at",
            "subscription_status",
        ]
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    if not _stripe_configured():
        return Response(
            {"error": "Stripe is not configured"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    stripe.api_key = settings.STRIPE_SECRET_KEY

    plan = (request.data.get("plan") or "").strip().lower()
    parent_email = (request.data.get("parent_email") or "").strip()
    student_id = request.data.get("student_id")

    try:
        student_id = int(student_id)
    except (TypeError, ValueError):
        return Response({"error": "student_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    if student_id != request.user.pk:
        return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    if plan not in ("monthly", "annual"):
        return Response({"error": "plan must be monthly or annual"}, status=status.HTTP_400_BAD_REQUEST)

    if not parent_email:
        return Response({"error": "parent_email is required"}, status=status.HTTP_400_BAD_REQUEST)

    price_id = (
        settings.STRIPE_MONTHLY_PRICE_ID if plan == "monthly" else settings.STRIPE_ANNUAL_PRICE_ID
    )
    if not price_id:
        return Response(
            {"error": "Price not configured for this plan"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    existing = stripe.Customer.list(email=parent_email, limit=1)
    if existing.data:
        customer = existing.data[0]
    else:
        customer = stripe.Customer.create(email=parent_email)

    student = request.user
    student.parent_email = parent_email
    student.save(update_fields=["parent_email"])

    success_url = request.build_absolute_uri("/billing/success/?session_id={CHECKOUT_SESSION_ID}")
    cancel_url = request.build_absolute_uri("/billing/cancel/")

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer.id,
        line_items=[{"price": price_id, "quantity": 1}],
        metadata={"student_id": str(student_id)},
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return Response({"checkout_url": session.url})


@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not _stripe_configured():
        return HttpResponse(status=200)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    wh_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "") or ""

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, wh_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    etype = event["type"]
    data_object = event["data"]["object"]

    if etype == "checkout.session.completed":
        session = data_object
        meta = session.get("metadata") or {}
        sid = meta.get("student_id")
        if not sid:
            return HttpResponse(status=200)
        try:
            student = User.objects.get(pk=int(sid))
        except (User.DoesNotExist, ValueError, TypeError):
            return HttpResponse(status=200)

        sub_id = session.get("subscription")
        cust_id = session.get("customer")
        if cust_id:
            student.stripe_customer_id = cust_id
        if sub_id:
            student.stripe_subscription_id = sub_id
            sub = stripe.Subscription.retrieve(sub_id)
            items = sub.get("items", {}).get("data") or []
            price_id = items[0].get("price", {}).get("id") if items else None
            _apply_subscription_from_stripe_subscription(student, sub, price_id=price_id)
        else:
            student.save(update_fields=["stripe_customer_id", "stripe_subscription_id"])

    elif etype == "customer.subscription.updated":
        sub = data_object
        sub_id = sub.get("id")
        try:
            student = User.objects.get(stripe_subscription_id=sub_id)
        except User.DoesNotExist:
            cust = sub.get("customer")
            if not cust:
                return HttpResponse(status=200)
            try:
                student = User.objects.get(stripe_customer_id=cust)
            except User.DoesNotExist:
                return HttpResponse(status=200)
        items = sub.get("items", {}).get("data") or []
        price_id = items[0].get("price", {}).get("id") if items else None
        _apply_subscription_from_stripe_subscription(student, sub, price_id=price_id)

    elif etype == "customer.subscription.deleted":
        sub = data_object
        sub_id = sub.get("id")
        try:
            student = User.objects.get(stripe_subscription_id=sub_id)
        except User.DoesNotExist:
            return HttpResponse(status=200)
        student.subscription_status = "cancelled"
        student.save(update_fields=["subscription_status"])

    return HttpResponse(status=200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def billing_status(request):
    u = request.user
    return Response(
        {
            "subscription_status": getattr(u, "subscription_status", "free"),
            "is_pro": u.is_pro,
        }
    )


def billing_success_page(request):
    return render(request, "billing_success.html")


def billing_cancel_page(request):
    return render(request, "billing_cancel.html")
