from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from .config import config

engine = create_async_engine(config.DATABASE_URL)

async def get_db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


from typing import Annotated
from fastapi import Depends
SessionDep = Annotated[AsyncSession, Depends(get_db)]


