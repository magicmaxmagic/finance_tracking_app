"""Repository for onboarding profile."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.onboarding import OnboardingProfile


class OnboardingRepository:
    """Onboarding profile repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user(self, user_id: int) -> OnboardingProfile | None:
        result = await self.session.execute(
            select(OnboardingProfile).where(OnboardingProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, **kwargs) -> OnboardingProfile:
        profile = OnboardingProfile(user_id=user_id, **kwargs)
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def update(self, profile: OnboardingProfile, **kwargs) -> OnboardingProfile:
        for key, value in kwargs.items():
            if value is not None:
                setattr(profile, key, value)
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile
