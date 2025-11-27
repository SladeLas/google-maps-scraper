'''Creates database'''

import psycopg2
from dustly.core.config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT

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
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        ),

        ('entities', """
         CREATE TABLE IF NOT EXISTS scrape_history (
                id BIGSERIAL PRIMARY KEY,
                name TEXT,
                place_id TEXT,
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
        CREATE TABLE IF NOT EXISTS scrape_history (
            id BIGSERIAL PRIMARY KEY,
            entity_id INT,
            first_name TEXT,
            last_name TEXT,
            title TEXT,
            phone TEXT,
            email TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            
            FOREIGN KEY (entity_id) REFERENCES entities(id)
            """
        )
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
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s)",
                (table_name,)
            )
            exists_result = cursor.fetchone()
            exists = exists_result[0] if exists_result else False  # Fixing the issue here

            if exists:
                print(f"Table '{table_name}' already exists. Skipping creation.")
            else:
                cursor.execute(command)
                print(f"Executed creation command for table '{table_name}':\n{command}")

        cursor.close()
        connection.close()
        print("Tables checked/created successfully.")

    except (psycopg2.Error, ValueError) as error:
        print("Error creating tables:", error)

if __name__ == '__main__':
    if test_connection():
        print("Connected.")
        create_tables()
    else:
        print("Connection Failed.")
