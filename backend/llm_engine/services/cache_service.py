import sqlite3
import hashlib
import json
import os

class CacheService:
    def __init__(self, db_path="llm_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS llm_cache (
                prompt_hash TEXT PRIMARY KEY,
                response TEXT,
                model_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def _hash_prompt(self, prompt: str, model_name: str) -> str:
        return hashlib.sha256(f"{prompt}_{model_name}".encode('utf-8')).hexdigest()

    def get(self, prompt: str, model_name: str):
        prompt_hash = self._hash_prompt(prompt, model_name)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT response FROM llm_cache WHERE prompt_hash = ?', (prompt_hash,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None

    def set(self, prompt: str, model_name: str, response: dict):
        prompt_hash = self._hash_prompt(prompt, model_name)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO llm_cache (prompt_hash, response, model_name)
            VALUES (?, ?, ?)
        ''', (prompt_hash, json.dumps(response), model_name))
        conn.commit()
        conn.close()
