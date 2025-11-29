'''Creates database'''

import psycopg2
from slade_digital_scrapers.core.config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT

def test_connection():
    """
    Test the connection to the Supabase PostgreSQL database.
    Returns:
    bool: True if connection is successful, False otherwise.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        # Create a cursor and execute a test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print("Connected to PostgreSQL version:", db_version)

        # Clean up
        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        print("Failed to connect to the database:", e)
        return False

def create_tables():

    """Create tables in the PostgreSQL database if they do not exist."""

    tables = [
        ('scrape_history', """
            CREATE TABLE IF NOT EXISTS scrape_history (
                id BIGSERIAL PRIMARY KEY,
                source TEXT NOT NULL UNIQUE,
                search_key TEXT,
                location_key TEXT,
                results_scraped INT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        ),

        ('entities', """
         CREATE TABLE IF NOT EXISTS entities (
                id BIGSERIAL PRIMARY KEY,
                name TEXT,
                place_id TEXT UNIQUE,
                address TEXT,
                google_rating INT,
                review_count INT,
                entity_categories TEXT[],
                website TEXT,
                phone TEXT,
                google_link TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
         """),

        ('contacts', """
        CREATE TABLE IF NOT EXISTS contacts (
            id BIGSERIAL PRIMARY KEY,
            entity_id INT,
            first_name TEXT,
            last_name TEXT,
            title TEXT,
            phone TEXT,
            email TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            
            FOREIGN KEY (entity_id) REFERENCES entities(id)
        );
        """),
        ('jobs', """
        CREATE TABLE IF NOT EXISTS jobs (
            id BIGSERIAL PRIMARY KEY,
            linkedin_url TEXT,
            job_title TEXT,
            company TEXT,
            company_linkedin_url TEXT,
            location TEXT,
            posted_date DATE,
            application_count INT,
            job_description TEXT,
            benefits TEXT
        );
        """),
    ]

    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        connection.autocommit = True
        cursor = connection.cursor()

        for table_name, command in tables:
            # Check if the table exists in the public schema.
            cursor.execute(
                """SELECT EXISTS 
                (SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
                )""",
                (table_name,)
            )
            exists_result = cursor.fetchone()
            exists = exists_result[0] if exists_result else False  # Fixing the issue here

            if exists:
                print(f"Table '{table_name}' already exists. Skipping creation.")
            else:
                cursor.execute(command)
                print(f"Executed creation command for table '{table_name}':\n{command}")

        # Ensure unique constraints exist
        _ensure_constraints(cursor)
        
        cursor.close()
        connection.close()
        print("Tables checked/created successfully.")

    except (psycopg2.Error, ValueError) as error:
        print("Error creating tables:", error)


def _ensure_constraints(cursor):
    """Ensure unique constraints exist on required columns."""
    constraints = [
        {
            "table": "entities",
            "column": "place_id",
            "constraint_name": "entities_place_id_key",
            "sql": "ALTER TABLE entities ADD CONSTRAINT entities_place_id_key UNIQUE (place_id);"
        },
    ]
    
    for constraint in constraints:
        try:
            # Check if constraint already exists
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1 
                    FROM pg_constraint 
                    WHERE conname = %s
                )
                """,
                (constraint["constraint_name"],)
            )
            exists = cursor.fetchone()[0]
            
            if not exists:
                cursor.execute(constraint["sql"])
                print(f"Added unique constraint '{constraint['constraint_name']}' to {constraint['table']}.{constraint['column']}")
            else:
                print(f"Constraint '{constraint['constraint_name']}' already exists on {constraint['table']}.{constraint['column']}")
        except psycopg2.Error as e:
            # Constraint might already exist or table might not exist yet
            if "already exists" not in str(e).lower():
                print(f"Warning: Could not add constraint '{constraint['constraint_name']}': {e}")


if __name__ == '__main__':
    if test_connection():
        print("Connected.")
        create_tables()
    else:
        print("Connection Failed.")
