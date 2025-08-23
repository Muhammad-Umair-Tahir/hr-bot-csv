import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

load_dotenv()

_async_engine = None
_async_session_maker = None

def get_async_engine():
    global _async_engine
    if _async_engine is None:
        connection_string = os.getenv("DATABASE_URL")
        if not connection_string:
            raise ValueError("DATABASE_URL not set in .env")

        # Ensure it's asyncpg for Supabase
        if connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

        _async_engine = create_async_engine(
            connection_string,
            echo=False,          # Change to True for SQL logging
            pool_size=10,
            max_overflow=20
        )
        print("SQLAlchemy Async Engine created.")
    return _async_engine

def get_async_session_maker():
    global _async_session_maker
    if _async_session_maker is None:
        engine = get_async_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
        print("SQLAlchemy Async Session Maker created.")
    return _async_session_maker

async def get_db_session():
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        yield session

async def dispose_engine():
    global _async_engine
    if _async_engine:
        print("Disposing SQLAlchemy Async Engine...")
        await _async_engine.dispose()
        _async_engine = None
        print("SQLAlchemy Async Engine disposed.")

async def init_db():
    get_async_engine()
    get_async_session_maker()

async def close_db():
    await dispose_engine()

# Test connection directly
async def main():
    try:
        session_maker = get_async_session_maker()
        async with session_maker() as session:
            print("Testing connection to database...")
            result = await session.execute(text('SELECT version();'))
            version = result.scalar_one()
            print(f"Connected successfully. PostgreSQL version: {version}")
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        await dispose_engine()

if __name__ == "__main__":
    asyncio.run(main())
