"""Script to create the initial user."""

import logging
from core.auth import get_password_hash
from core.database import get_conn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_initial_user():
    username = "vinicius.andrade"
    password = "@2026pwd"
    email = "vinicius.andrade@deepcode.vsa"
    
    hashed_password = get_password_hash(password)
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Check if user exists
                cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    logger.info(f"User {username} already exists.")
                    return
                
                cur.execute(
                    "INSERT INTO users (username, hashed_password, email) VALUES (%s, %s, %s)",
                    (username, hashed_password, email)
                )
                conn.commit()
                logger.info(f"User {username} created successfully.")
    except Exception as e:
        logger.error(f"Error creating user: {e}")

if __name__ == "__main__":
    create_initial_user()
