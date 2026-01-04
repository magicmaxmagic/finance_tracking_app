"""Service for user settings."""
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_settings import UserSettings
from app.repositories.settings import SettingsRepository
from app.repositories.subscription import SubscriptionRepository
from app.schemas.settings import SettingsResponse, SettingsUpdate, PlanEnum, SubscriptionStatusEnum


DEFAULT_SETTINGS = {
    "currency": "USD",
    "timezone": "America/New_York",
    "date_format": "MM/DD/YYYY",
    "start_of_week": "Monday",
    "default_view": "dashboard",
    "data_retention": "forever",
    "digest_enabled": True,
    "transaction_alerts": True,
    "budget_alerts": True,
    "auto_categorization": True,
    "import_deduplication": True,
    "analytics_opt_in": True,
    "planning_preferences": None,
}


class SettingsService:
    """Service layer for user settings."""

    def __init__(self, session: AsyncSession):
        self.repository = SettingsRepository(session)
        self.subscription_repository = SubscriptionRepository(session)

    async def get_settings(self, user_id: int) -> SettingsResponse:
        settings = await self.repository.get_by_user(user_id)
        if not settings:
            settings = await self.repository.create(user_id=user_id, **DEFAULT_SETTINGS)
        settings = await self._ensure_calendar_feed_token(settings)
        return await self._hydrate_subscription(settings, user_id)

    async def update_settings(self, user_id: int, payload: SettingsUpdate) -> SettingsResponse:
        settings = await self.repository.get_by_user(user_id)
        if not settings:
            settings = await self.repository.create(user_id=user_id, **DEFAULT_SETTINGS)
        update_data = payload.dict(exclude_unset=True)
        settings = await self.repository.update(settings, **update_data)
        settings = await self._ensure_calendar_feed_token(settings)
        return await self._hydrate_subscription(settings, user_id)

    async def rotate_calendar_feed_token(self, user_id: int) -> SettingsResponse:
        settings = await self.repository.get_by_user(user_id)
        if not settings:
            settings = await self.repository.create(user_id=user_id, **DEFAULT_SETTINGS)
        settings = await self.repository.update(
            settings,
            calendar_feed_token=self._generate_calendar_token(),
        )
        return await self._hydrate_subscription(settings, user_id)

    async def get_settings_by_calendar_token(self, token: str) -> UserSettings | None:
        if not token:
            return None
        return await self.repository.get_by_calendar_feed_token(token)

    def _generate_calendar_token(self) -> str:
        return secrets.token_hex(32)

    async def _ensure_calendar_feed_token(self, settings):
        if not settings.calendar_feed_token:
            settings = await self.repository.update(
                settings,
                calendar_feed_token=self._generate_calendar_token(),
            )
        return settings

    async def _hydrate_subscription(self, settings, user_id: int) -> SettingsResponse:
        subscription = await self.subscription_repository.get_by_user(user_id)
        plan = PlanEnum.STARTER
        status = None
        current_period_end = None
        cancel_at_period_end = None

        if subscription:
            if subscription.status:
                status_value = subscription.status.value if hasattr(subscription.status, "value") else subscription.status
                status = SubscriptionStatusEnum(status_value)
            if subscription.plan:
                plan_value = subscription.plan.value if hasattr(subscription.plan, "value") else subscription.plan
                plan = PlanEnum(plan_value)
            current_period_end = subscription.current_period_end
            cancel_at_period_end = subscription.cancel_at_period_end

        response = SettingsResponse.model_validate(settings, from_attributes=True)
        return response.model_copy(
            update={
                "plan": plan,
                "subscription_status": status,
                "current_period_end": current_period_end,
                "cancel_at_period_end": cancel_at_period_end,
            }
        )
