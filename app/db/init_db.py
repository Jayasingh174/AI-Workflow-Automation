import asyncio
from app.db.session import engine
from app.db.model import Base

async def init_models():
    print("Connecting to PostgreSQL...")
    
    # We open an asynchronous connection block
    async with engine.begin() as conn:
        # We tell the async connection to run the synchronous create_all method
        await conn.run_sync(Base.metadata.create_all)
        
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    # Execute the async function using asyncio
    asyncio.run(init_models())