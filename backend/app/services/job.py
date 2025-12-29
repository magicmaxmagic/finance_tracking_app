"""Job service for background task tracking."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.job import JobRepository
from app.models.job import Job


class JobService:
    """Service for job operations."""

    def __init__(self, session: AsyncSession):
        self.repository = JobRepository(session)
        self.session = session

    async def create_job(self, user_id: int, job_type: str, payload: dict | None = None) -> Job:
        return await self.repository.create(user_id=user_id, job_type=job_type, payload=payload)

    async def get_job(self, job_id: int, user_id: int) -> Job | None:
        return await self.repository.get_by_id(job_id, user_id)

    async def update_status(self, job: Job, status: str, result: dict | None = None, error: str | None = None) -> Job:
        return await self.repository.update_status(job, status, result=result, error=error)
