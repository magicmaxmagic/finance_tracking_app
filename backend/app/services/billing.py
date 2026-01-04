"""Billing service for Stripe checkout and subscription sync."""
from datetime import datetime
from typing import Any
import stripe
from starlette.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.subscription import SubscriptionPlan, SubscriptionStatus
from app.repositories.subscription import SubscriptionRepository
from app.schemas.billing import BillingInterval


class BillingService:
    """Service for Stripe billing operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = SubscriptionRepository(session)
        stripe.api_key = settings.STRIPE_SECRET_KEY

    async def create_checkout_session(self, user_id: int, email: str, interval: BillingInterval) -> str:
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("Stripe secret key is not configured.")
        price_id = self._resolve_price_id(interval)
        subscription = await self.repository.get_by_user(user_id)

        params: dict[str, Any] = {
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": settings.STRIPE_SUCCESS_URL,
            "cancel_url": settings.STRIPE_CANCEL_URL,
            "client_reference_id": str(user_id),
            "metadata": {"user_id": str(user_id)},
            "subscription_data": {"metadata": {"user_id": str(user_id)}},
            "allow_promotion_codes": True,
        }

        if subscription and subscription.stripe_customer_id:
            params["customer"] = subscription.stripe_customer_id
        else:
            params["customer_email"] = email

        session = await run_in_threadpool(stripe.checkout.Session.create, **params)

        if subscription and session.get("customer") and not subscription.stripe_customer_id:
            await self.repository.update(subscription, stripe_customer_id=session["customer"])

        return session["url"]

    async def create_portal_session(self, user_id: int) -> str:
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("Stripe secret key is not configured.")
        subscription = await self.repository.get_by_user(user_id)
        if not subscription or not subscription.stripe_customer_id:
            raise ValueError("No Stripe customer found for user.")

        portal = await run_in_threadpool(
            stripe.billing_portal.Session.create,
            customer=subscription.stripe_customer_id,
            return_url=settings.STRIPE_PORTAL_RETURN_URL,
        )
        return portal["url"]

    async def handle_webhook(self, event: stripe.Event) -> None:
        event_type = event.get("type")
        data_object = event.get("data", {}).get("object")

        if not event_type or not data_object:
            return

        if event_type == "checkout.session.completed":
            subscription_id = data_object.get("subscription")
            if subscription_id:
                subscription = await run_in_threadpool(stripe.Subscription.retrieve, subscription_id, expand=["items.data.price"])
                await self._sync_subscription(subscription, user_id=self._extract_user_id(data_object))
            return

        if event_type.startswith("customer.subscription."):
            await self._sync_subscription(data_object)

    def _resolve_price_id(self, interval: BillingInterval) -> str:
        if interval == BillingInterval.ANNUAL:
            price_id = settings.STRIPE_PRICE_ID_PRO_ANNUAL
        else:
            price_id = settings.STRIPE_PRICE_ID_PRO_MONTHLY
        if not price_id:
            raise ValueError("Stripe price ID is not configured.")
        return price_id

    async def _sync_subscription(self, subscription: Any, user_id: int | None = None) -> None:
        metadata = subscription.get("metadata") or {}
        user_id = user_id or self._coerce_user_id(metadata.get("user_id"))

        stripe_subscription_id = subscription.get("id")
        stripe_customer_id = subscription.get("customer")
        stripe_price_id = None
        items = subscription.get("items", {}).get("data") if subscription.get("items") else None
        if items:
            stripe_price_id = items[0].get("price", {}).get("id")

        status_value = subscription.get("status")
        status = None
        if status_value:
            try:
                status = SubscriptionStatus(status_value)
            except ValueError:
                status = None

        current_period_end = None
        if subscription.get("current_period_end"):
            current_period_end = datetime.utcfromtimestamp(subscription["current_period_end"])

        plan = SubscriptionPlan.PRO if status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING} else SubscriptionPlan.STARTER
        cancel_at_period_end = bool(subscription.get("cancel_at_period_end", False))

        if not user_id:
            existing = None
            if stripe_subscription_id:
                existing = await self.repository.get_by_subscription_id(stripe_subscription_id)
            if not existing and stripe_customer_id:
                existing = await self.repository.get_by_customer_id(stripe_customer_id)
            if not existing:
                return
            user_id = existing.user_id

        existing = await self.repository.get_by_user(user_id)
        data = {
            "plan": plan,
            "status": status,
            "stripe_customer_id": stripe_customer_id,
            "stripe_subscription_id": stripe_subscription_id,
            "stripe_price_id": stripe_price_id,
            "current_period_end": current_period_end,
            "cancel_at_period_end": cancel_at_period_end,
        }

        if existing:
            await self.repository.update(existing, **data)
        else:
            await self.repository.create(user_id=user_id, **data)

    def _extract_user_id(self, session: dict[str, Any]) -> int | None:
        metadata = session.get("metadata") or {}
        return self._coerce_user_id(metadata.get("user_id"))

    def _coerce_user_id(self, value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
