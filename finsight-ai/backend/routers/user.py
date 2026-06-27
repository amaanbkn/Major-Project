from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from dependencies import get_current_user
import sqlite3
import os

router = APIRouter()

class UserSettingsUpdate(BaseModel):
    display_name: str
    balance: float

@router.get("/user/settings")
async def get_user_settings(current_user: str = Depends(get_current_user)):
    db_path = os.getenv("SQLITE_DB_PATH", "./finsight.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Get settings
        row = conn.execute("SELECT display_name FROM user_settings WHERE user_id = ?", (current_user,)).fetchone()
        display_name = row["display_name"] if row else "Amaan Siddiqui"

        # Get balance
        balance_row = conn.execute("SELECT balance FROM virtual_balance WHERE user_id = ?", (current_user,)).fetchone()
        balance = balance_row["balance"] if balance_row else 100000.0

        return {
            "user_id": current_user,
            "display_name": display_name,
            "balance": balance,
            "api_keys": {
                "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "missing",
                "supabase": "configured" if os.getenv("VITE_SUPABASE_URL") and os.getenv("VITE_SUPABASE_ANON_KEY") else "missing"
            }
        }
    finally:
        conn.close()

@router.put("/user/settings")
async def update_user_settings(data: UserSettingsUpdate, current_user: str = Depends(get_current_user)):
    db_path = os.getenv("SQLITE_DB_PATH", "./finsight.db")
    conn = sqlite3.connect(db_path)
    try:
        # Update/insert display name
        conn.execute("""
            INSERT INTO user_settings (user_id, display_name)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET display_name = excluded.display_name, updated_at = datetime('now')
        """, (current_user, data.display_name))

        # Update balance
        conn.execute("""
            INSERT INTO virtual_balance (user_id, balance)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET balance = excluded.balance, updated_at = datetime('now')
        """, (current_user, data.balance))

        conn.commit()
        return {"status": "success", "message": "Settings updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
