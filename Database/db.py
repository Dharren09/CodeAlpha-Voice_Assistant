import sqlite3

class VoiceAssistantDB:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS queries (id INTEGER PRIMARY KEY, query TEXT)''')
        self.conn.commit()

    def insert_query(self, query):
        self.cursor.execute("INSERT INTO queries (query) VALUES (?)", (query,))
        self.conn.commit()

    def get_query_history(self):
        self.cursor.execute("SELECT query FROM queries")
        rows = self.cursor.fetchall()
        return [row[0] for row in rows]

    def close(self):
        self.conn.close()
