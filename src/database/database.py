import sqlite3
from datetime import datetime
from config.config import DATABASE_NAME, DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_ID, logger

def init_database():
    """Initialize database and create necessary tables"""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    
    # Create offers table
    c.execute('''CREATE TABLE IF NOT EXISTS offers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  description TEXT,
                  payout REAL,
                  geo TEXT,
                  vertical TEXT,
                  kpi TEXT,
                  tracker TEXT,
                  antifraud TEXT,
                  created_at TIMESTAMP,
                  appsflyer_offer_id TEXT,
                  event_name TEXT)''')
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  role TEXT DEFAULT 'partner',
                  created_at TIMESTAMP)''')

    # Check for event_name column
    c.execute("PRAGMA table_info(offers)")
    columns = [col[1] for col in c.fetchall()]
    if 'event_name' not in columns:
        c.execute("ALTER TABLE offers ADD COLUMN event_name TEXT")

    # Add default admin
    try:
        c.execute("INSERT INTO users (user_id, username, role, created_at) VALUES (?, ?, ?, ?)",
                  (DEFAULT_ADMIN_ID, DEFAULT_ADMIN_USERNAME, 'admin', datetime.now().isoformat()))
    except sqlite3.IntegrityError:
        pass

    conn.commit()
    conn.close()

def get_user_role(user_id: int) -> str:
    """Get user role from database"""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE user_id=?", (user_id,))
    role = c.fetchone()
    conn.close()
    return role[0] if role else 'partner'

def add_offer_to_db(offer_data: dict):
    """Add new offer to database"""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO offers
                 (name, description, payout, geo, vertical,
                  kpi, tracker, antifraud, created_at, appsflyer_offer_id, event_name)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (offer_data['name'],
               offer_data['description'],
               offer_data['payout'],
               offer_data['geo'],
               offer_data['vertical'],
               offer_data['kpi'],
               offer_data['tracker'],
               offer_data['antifraud'],
               datetime.now(),
               offer_data['appsflyer_offer_id'],
               offer_data['event_name']))
    conn.commit()
    conn.close()

def get_all_offers():
    """Get all offers from database"""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM offers")
    offers = c.fetchall()
    conn.close()
    return offers

def get_offer_details(offer_id: int):
    """Get specific offer details"""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM offers WHERE id=?", (offer_id,))
    offer = c.fetchone()
    conn.close()
    return offer

def update_offer(offer_id: int, field: str, value: str):
    """Update specific offer field"""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute(f"UPDATE offers SET {field}=? WHERE id=?", (value, offer_id))
    conn.commit()
    conn.close()

def delete_offer(offer_id: int):
    """Delete offer from database"""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM offers WHERE id=?", (offer_id,))
    conn.commit()
    conn.close()

def update_user_role(username: str, new_role: str) -> bool:
    """Update user role in database"""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET role=? WHERE username=?", (new_role, username))
    success = c.rowcount > 0
    conn.commit()
    conn.close()
    return success

def create_user(user_id: int, username: str, role: str = 'partner'):
    """Create new user in database"""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO users
                     (user_id, username, role, created_at)
                     VALUES (?, ?, ?, ?)''',
                 (user_id, username, role, datetime.now()))
        conn.commit()
    except sqlite3.IntegrityError:
        logger.warning(f"User {username} already exists")
    finally:
        conn.close() 