import uuid
from datetime import datetime
from db import get_connection

class PauseRecord:
    def __init__(self, session_id: str, pause_reason: str):
        self.pause_id = str(uuid.uuid4())
        self.session_id = session_id
        self.pause_reason = pause_reason
        self.paused_at = datetime.now()
        self.resumed_at = None
        self.pause_seconds = None

    def resume(self):
        self.resumed_at = datetime.now()
        self.pause_seconds = int((self.resumed_at - self.paused_at).total_seconds())

    def save(self):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO PAUSE_RECORDS (pause_id, session_id, pause_reason,
                    paused_at, resumed_at, pause_seconds)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (self.pause_id, self.session_id, self.pause_reason,
                  self.paused_at, self.resumed_at, self.pause_seconds))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def update_resume(self):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE PAUSE_RECORDS SET resumed_at = %s, pause_seconds = %s
                WHERE pause_id = %s
            """, (self.resumed_at, self.pause_seconds, self.pause_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def find_by_session(session_id: str):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM PAUSE_RECORDS WHERE session_id = %s", (session_id,))
            return cursor.fetchall()  # one-to-many: multiple pauses per session
        finally:
            cursor.close()
            conn.close()

class PauseHistory:
    def __init__(self, session_id:str):
        self.session_id = session_id
        self.pauses = list = []

    def add(self, pause:PauseRecord):
        self.pauses.append(pause)

    def get_total_pause_seconds(self) -> int :
        return sum(
            p.pause_seconds for p in self.pauses
            if p.pause_seconds is not None
        )
    
    def get_active_pause(self):
        for p in self.pauses:
            if p.resumed_at is None:
                return p
            
        return None
    def is_currently_paused(self) -> bool:
        return self.get_active_pause() is not None

    def get_pause_count(self) -> int:
        return len(self.pauses)

    def get_average_pause_seconds(self) -> float:
        completed = [p for p in self.pauses if p.pause_seconds is not None]
        if not completed:
            return 0.0
        return round(sum(p.pause_seconds for p in completed) / len(completed), 2)
    
    def get_summary(self) -> dict:
        return {
            "session_id":           self.session_id,
            "total_pauses":         self.get_pause_count(),
            "total_pause_seconds":  self.get_total_pause_seconds(),
            "avg_pause_seconds":    self.get_average_pause_seconds(),
            "is_currently_paused":  self.is_currently_paused(),
        }

    @classmethod
    def load_from_db(cls, session_id: str) -> "PauseHistory":
        """
        Rebuilds a PauseHistory from DB rows for a session.
        Useful when resuming a session that was previously active.
        """
        history = cls(session_id)
        rows    = PauseRecord.find_by_session(session_id)
        for row in rows:
            p             = PauseRecord.__new__(PauseRecord)
            p.pause_id    = row["pause_id"]
            p.session_id  = row["session_id"]
            p.pause_reason = row["pause_reason"]
            p.paused_at   = row["paused_at"]
            p.resumed_at  = row["resumed_at"]
            p.pause_seconds = row["pause_seconds"]
            history.add(p)
        return history