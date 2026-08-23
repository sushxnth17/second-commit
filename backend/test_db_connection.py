from sqlalchemy import text
from app.database.database import engine

def inspect_repo():
    print("Querying 'repositories' table in the database...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM repositories")).fetchall()
            print(f"Total rows found: {len(result)}")
            for row in result:
                # Get column keys
                keys = row._mapping.keys()
                print("\nRepository Row:")
                for k in keys:
                    print(f"  {k}: {row._mapping[k]}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    inspect_repo()
