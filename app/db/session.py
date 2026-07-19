import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Best practice: Load this from a .env file in the future
# DATABASE_URL = os.getenv("DATABASE_URL") 
DATABASE_URL = "postgresql+asyncpg://postgres:Jaya@123@localhost:5432/postgres"

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Use the modern async_sessionmaker
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Dependency to yield the database session
async def get_db():
    async with async_session_maker() as session:
        yield session