"""Standalone database initialization script."""
import sys
from app.db.session import Base, engine
import app.models

def init_database():
    print(f"Connecting to database via: {engine.url.render_as_string(hide_password=True)}")
    print("Creating all database tables according to SQLAlchemy metadata...")
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")

if __name__ == "__main__":
    init_database()
