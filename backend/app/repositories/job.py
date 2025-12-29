"""Job repository."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.job import Job


class JobRepository:
    """Repository for background jobs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, job_type: str, payload: dict | None = None) -> Job:
        job = Job(user_id=user_id, job_type=job_type, payload=payload)
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_by_id(self, job_id: int, user_id: int) -> Job | None:
        result = await self.session.execute(
            select(Job).where(Job.id == job_id, Job.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, job: Job, status: str, result: dict | None = None, error: str | None = None) -> Job:
        job.status = status
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job
