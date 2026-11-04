from sqlalchemy import create_engine, text
from app.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)


def test_connection():

    try:
        with engine.connect() as connection:

            result = connection.execute(
                text("""
                    SELECT
                        current_database(),
                        current_user,
                        PostGIS_Full_Version();
                """)
            )

            print("Database connection successful!")

            for row in result:
                print("Database:", row[0])
                print("User:", row[1])
                print("PostGIS:", row[2])

    except Exception as error:
        print("Database connection failed!")
        print(error)