import logging
import sys
from pathlib import Path
from typing import List, Optional

import mariadb

from .app_types import ERROR_ENTRY_EXISTS, ERROR_MARIA_DB, DatasetEntry

logger = logging.getLogger("firestorm_bot")

CURRENT_DIR = str(Path(__file__).resolve().parent)

class Db:
    """
    Wrapper around Database Operations
    """
    def __init__(self,
        password: str,
        host: str = "127.0.0.1",
        user: str = "root",
        port: int = 3306,
        database: str = "bingo-dataset"
    ):
        try:
            conn = mariadb.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database=database,
                reconnect=True

            )
            self.conn = conn
            self.cur = conn.cursor()
            logger.info(f"Successfully connected to {database}!")

            # Run migrations/database initializations
            with open(f'{CURRENT_DIR}/schema.sql', 'r', encoding='utf-8') as f:
                sql_script = f.read()
                self.cur.execute(sql_script)
                conn.commit()
                logger.info("Database successfully migrated.")
        except mariadb.OperationalError as e:
            logger.error(f"DB connection error: {e}")
            sys.exit(1)
        except mariadb.Error as e:
            logger.error(f"DB error: {e}")
            sys.exit(1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cur.close()
        self.conn.close()

    def add_prompt(self, pool: str, prompt: str, weight: int, sensitivity: str, flags: str) -> int:
        """
        Returns ID of the last row inserted.
        """
        try:
            # First check whether the prompt exists in this pool.
            self.cur.execute(
                "SELECT 1 FROM dataset where pool = %s AND prompt = %s LIMIT 1",
                (pool, prompt)
            )
            result = self.cur.fetchone()
            # If fetchone is not None, that means prompt exists in pool.
            if result:
                return ERROR_ENTRY_EXISTS
            # Now add the entry.
            self.cur.execute(
                "INSERT INTO dataset (pool, prompt, weight, sensitivity, flags, approved) VALUES (?, ?, ?, ?, ?, ?)",
                (pool, prompt, weight, sensitivity, flags, False)
            )
            self.conn.commit()
            return self.cur.lastrowid
        except mariadb.Error as e:
            logger.warning(f"Error adding prompt: {e}")
            return ERROR_MARIA_DB

    def approve_prompt(self, uid: int) -> bool:
        """
        Assumptions: user privilege has already been checked beforehand.
        """
        try:
            self.cur.execute("UPDATE dataset SET approved = 1 WHERE id = ?", (uid,))
            self.conn.commit()
            return True
        except mariadb.Error as e:
            logger.warning(f"Failed to approve {id}: {e}")
            return False

    def reject_prompt(self, uid: int, reason: str) -> bool:
        """
        Assumptions: user privilege has already been checked beforehand.
        """
        try:
            self.cur.execute(
                "UPDATE dataset SET rejected = 1, reject_reason = ? WHERE id = ?",
                (reason, uid)
            )
            self.conn.commit()
            return True
        except mariadb.Error as e:
            logger.warning(f"Failed to reject {id}: {e}")
            return False

    def modify_prompt(
        self,
        uid: int,
        is_privileged_role: bool,
        prompt: Optional[str],
        weight: Optional[int],
        sensitivity: Optional[str],
        flags: Optional[str]
    ) -> Optional[DatasetEntry]:
        """
        If privileged user, allow them to edit from dataset arbitrarily.
        If non-privileged user, only allow editing of unapproved entries that have not been rejected.
        """
        if not is_privileged_role:
            try:
                self.cur.execute("SELECT approved, rejected from dataset where id = ?", (uid,))
                approved, rejected = self.cur.fetchone()
                # If previously approved, reject.
                if approved == 1:
                    raise PermissionError("User does not have permission to modify an approved entry.")
                # Check that entry was not previously rejected.
                if rejected == 1:
                    raise PermissionError("Rejected entry cannot be modified!")
            except mariadb.Error as e:
                logger.warning(f"Error retrieving {uid}: {e}")
        try:
            if prompt:
                self.cur.execute("UPDATE dataset SET prompt = ? WHERE id = ?", (prompt, uid,))
            if weight:
                self.cur.execute("UPDATE dataset SET weight = ? WHERE id = ?", (weight, uid,))
            if sensitivity:
                self.cur.execute("UPDATE dataset SET sensitivity = ? WHERE id = ?", (sensitivity, uid,))
            if flags:
                self.cur.execute("UPDATE dataset SET flags = ? WHERE id = ?", (flags, uid,))
            self.conn.commit()

            # Return the new updated entry
            self.cur.execute("SELECT * FROM dataset WHERE id = ?", (uid,))
            row = self.cur.fetchone()
            entry = DatasetEntry(row[0], row[1], row[2], row[3], row[4], row[5] == 1, row[6], row[7] == 1)
            return entry
        except mariadb.Error as e:
            logger.warning(f"Failed to delete {id}: {e}")
            return None

    def delete_prompt(self, uid: int, is_privileged_role: bool) -> bool:
        """
        If privileged user, allow them to delete from dataset arbitrarily.
        If non-privileged user, only allow deleting of unapproved entries.
        """
        if not is_privileged_role:
            try:
                self.cur.execute("SELECT approved from dataset where id = ?", (uid,))
                approved = self.cur.fetchone()[0]
                # If previously approved, reject.
                if approved == 1:
                    raise PermissionError("Not privileged enough")
            except mariadb.Error as e:
                logger.warning(f"Error retrieving {uid}: {e}")
        try:
            self.cur.execute("DELETE FROM dataset WHERE id = ?", (uid,))
            self.conn.commit()
            return True
        except mariadb.Error as e:
            logger.warning(f"Failed to delete {id}: {e}")
            return False

    def get_pending_prompts(self) -> List[DatasetEntry]:
        entries = []
        try:
            self.cur.execute("SELECT * FROM dataset where approved = 0 AND rejected = 0")
            for row in self.cur:
                entry = DatasetEntry(row[0], row[1], row[2], row[3], row[4], row[5]==1, row[6])
                entries.append(entry)
        except mariadb.Error as e:
            logger.warning(f"Error retrieving pools: {e}")
        return entries

    def get_rejected_prompts(self) -> List[DatasetEntry]:
        entries = []
        try:
            self.cur.execute("SELECT * FROM dataset where approved = 0 AND rejected = 1")
            for row in self.cur:
                entry = DatasetEntry(
                    row[0], row[1], row[2], row[3], row[4], row[5]==1, row[6], row[7]==1, row[8], row[9]
                )
                entries.append(entry)
        except mariadb.Error as e:
            logger.warning(f"Error retrieving pools: {e}")
        return entries

    def get_pools(self) -> List[str]:
        pools = []
        try:
            self.cur.execute("SELECT DISTINCT pool FROM dataset where approved = 1")
            for row in self.cur:
                pools.append(row[0])
        except mariadb.Error as e:
            logger.warning(f"Error retrieving pools: {e}")
        return pools

    def show_pool(self, pool: str) -> List[DatasetEntry]:
        entries = []
        try:
            self.cur.execute("SELECT * FROM dataset WHERE pool = ? AND approved = 1", (pool,))
            for row in self.cur:
                entry = DatasetEntry(row[0], row[1], row[2], row[3], row[4], row[5]==1, row[6])
                entries.append(entry)
        except mariadb.Error as e:
            logger.warning(f"Error showing pool {pool}: {e}")
        return entries
