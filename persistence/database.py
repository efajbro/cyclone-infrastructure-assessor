import sqlite3
import json
import pandas as pd
import datetime
from config import Config
from models import AssessmentRecord


class DatabaseService:
    def __init__(self, db_path: str = Config.DB_PATH):
        self.db_path = db_path
        self.init_local_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_local_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS field_assessments
                     (hash_id TEXT PRIMARY KEY, created_at TEXT, updated_at TEXT, gps TEXT, infra_type TEXT, 
                      ai_severity TEXT, final_severity TEXT, total_cost REAL, sync_status TEXT, json_blob TEXT)"""
        )
        conn.commit()
        conn.close()

    def save_assessment(self, data: AssessmentRecord):
        conn = self.get_connection()
        cursor = conn.cursor()
        data_dict = data.model_dump()
        updated_at_ts = datetime.datetime.now().isoformat()

        cursor.execute(
            """INSERT INTO field_assessments (hash_id, created_at, updated_at, gps, infra_type, 
                                             ai_severity, final_severity, total_cost, sync_status, json_blob)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(hash_id) DO UPDATE SET
                   updated_at=excluded.updated_at,
                   final_severity=excluded.final_severity,
                   total_cost=excluded.total_cost,
                   sync_status=excluded.sync_status,
                   json_blob=excluded.json_blob""",
            (
                data.report_hash,
                data.created_at,
                updated_at_ts,
                data.gps,
                data.infra_type,
                data.ai_severity,
                data.final_severity,
                data.total_cost,
                "PENDING",
                json.dumps(data_dict),
            ),
        )
        conn.commit()
        conn.close()

    def get_all_assessments(self) -> pd.DataFrame:
        conn = self.get_connection()
        df = pd.read_sql_query(
            "SELECT hash_id, created_at, updated_at, infra_type, final_severity, total_cost, sync_status FROM field_assessments",
            conn,
        )
        conn.close()
        return df

    def sync_pending_records(self, updated_at_timestamp: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM field_assessments WHERE sync_status = 'PENDING'"
        )
        count = cursor.fetchone()[0]

        if count > 0:
            cursor.execute(
                "UPDATE field_assessments SET sync_status = 'SYNCED', updated_at = ? WHERE sync_status = 'PENDING'",
                (updated_at_timestamp,),
            )
            conn.commit()

        conn.close()
        return count

    def delete_assessment(self, hash_id: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM field_assessments WHERE hash_id = ?", (hash_id,))
        conn.commit()
        conn.close()
