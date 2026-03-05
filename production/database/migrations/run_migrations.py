# run_migrations.py
"""Database migration runner - applies SQL migrations in order."""
import asyncio
import os
import glob
import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fte_user:fte_password@localhost:5433/fte_db")


async def get_applied_migrations(conn) -> set:
    """Returns set of already-applied migration versions."""
    try:
        rows = await conn.fetch("SELECT version FROM schema_migrations")
        return {row["version"] for row in rows}
    except asyncpg.exceptions.UndefinedTableError:
        return set()


async def run_migrations():
    """Discovers and applies pending SQL migrations in order."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        applied = await get_applied_migrations(conn)
        print(f"Already applied migrations: {applied or 'none'}")

        migrations_dir = os.path.dirname(os.path.abspath(__file__))
        sql_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))

        for sql_file in sql_files:
            version = os.path.basename(sql_file).split("_")[0]
            if version in applied:
                print(f"  SKIP {os.path.basename(sql_file)} (already applied)")
                continue

            print(f"  APPLYING {os.path.basename(sql_file)}...")
            with open(sql_file, "r") as f:
                sql = f.read()
            await conn.execute(sql)
            print(f"  DONE {os.path.basename(sql_file)}")

        print("All migrations applied.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())
