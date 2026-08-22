"""
Script that takes a json prompts file, parses it, and stores the info into a given mariadb.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List

import mariadb
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

CURRENT_DIR = str(Path(__file__).resolve().parent)

class Db(object):
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

        except mariadb.OperationalError as e:
            logger.error(f"DB connection error: {e}")
            sys.exit(1)
        except mariadb.Error as e:
            logger.error(f"DB error: {e}")
            sys.exit(1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cur.close()
        self.conn.close()

    def add_prompts(self, pool: str, entries: List[Dict]) -> bool:
        """
        Returns True if managed to add all prompts to the DB,
        otherwise False if any fails.
        """
        insert_sql = "INSERT INTO dataset (pool, prompt, weight, sensitivity, enabled, flags, approved) VALUES (?, ?, ?, ?, ?, ?, ?)"
        prompts_to_insert = []
        for entry in entries:
            prompt = entry["text"]
            weight = entry["weight"] if "weight" in entry else 1
            sensitivity = entry["sensitivity"] if "sensitivity" in entry else "S"
            enabled = entry["enabled"] if "enabled" in entry else True
            flags = ",".join(entry["flags"]) if "flags" in entry else ""
            prompts_to_insert.append(
                (pool, prompt, weight, sensitivity, enabled, flags, True)
            )
        logger.info(f"Number of prompts found in dataset: {len(prompts_to_insert)}")
        logger.info("Attempting to store into database now...")
        try:
            self.cur.executemany(insert_sql, prompts_to_insert)
            self.conn.commit()
            logger.info(f"Successfully inserted {self.cur.rowcount} prompts into the database.")
            return True
        except mariadb.Error as e:
            logger.warning(f"Error adding prompt: {e}")
            return False

def parse_args():
    parser = argparse.ArgumentParser(
        description="Process a JSON dataset and adds it to an existing DB."
    )
    parser.add_argument('filename', help='The JSON file to be added to the database.')
    args = parser.parse_args()

    return args.filename

def main():
    load_dotenv(dotenv_path=f"{CURRENT_DIR}/.env")
    db_password = os.environ.get('DB_PASSWORD', '1234')
    db_user = os.environ.get('DB_USER', 'user')
    db_host = os.environ.get('DB_HOST', '127.0.0.1')
    db_port = int(os.environ.get('DB_PORT', 3306))
    default_db_name = os.environ.get('DEFAULT_DB', 'bingo-dataset')

    dataset_file = parse_args()
    dataset_name = dataset_file.strip(" ./").split(".")[0]

    logger.info(f"Processing {dataset_file}...")
    with open(dataset_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info("Connecting to db...")
    db = Db(db_password, db_host, db_user, db_port, default_db_name)

    db.add_prompts(dataset_name, data["entries"])


if __name__ == "__main__":
    main()
