import sqlite3
import os
import json
import threading
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path="data/astra.db"):
        """Initialize the database connection."""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.local = threading.local()
        self.initialize_db()

    def get_connection(self):
        """Get a thread-local database connection."""
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            self.local.conn = sqlite3.connect(self.db_path)
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn

    def initialize_db(self):
        """Initialize the database schema based on the configuration."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create the metric_triggers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metric_triggers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scid INTEGER NOT NULL,
            metric_type TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            value FLOAT NOT NULL,
            threshold FLOAT NOT NULL,
            status TEXT NOT NULL
        )
        ''')
        conn.commit()

    def log_trigger(self, scid, metric_type, timestamp, value, threshold, status):
        """Log a trigger event to the database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO metric_triggers (scid, metric_type, timestamp, value, threshold, status)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (scid, metric_type, timestamp, value, threshold, status))
        conn.commit()
        return cursor.lastrowid

    def get_all_triggers(self, limit=100, offset=0, sort_by="timestamp", sort_order="DESC", 
                         filters=None):
        """Get all trigger events with optional filtering and sorting."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM metric_triggers"
        params = []
        
        # Apply filters if provided
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if key == 'date_from' and value:
                    filter_conditions.append("timestamp >= ?")
                    params.append(value + " 00:00:00")  # Beginning of the day
                elif key == 'date_to' and value:
                    filter_conditions.append("timestamp <= ?")
                    params.append(value + " 23:59:59")  # End of the day
                elif value:
                    filter_conditions.append(f"{key} = ?")
                    params.append(value)
            
            if filter_conditions:
                query += " WHERE " + " AND ".join(filter_conditions)
        
        # Apply sorting
        query += f" ORDER BY {sort_by} {sort_order}"
        
        # Apply pagination
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_trigger_count(self, filters=None):
        """Get the total count of triggers with optional filtering."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) as count FROM metric_triggers"
        params = []
        
        # Apply filters if provided
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if key == 'date_from' and value:
                    filter_conditions.append("timestamp >= ?")
                    params.append(value + " 00:00:00")  # Beginning of the day
                elif key == 'date_to' and value:
                    filter_conditions.append("timestamp <= ?")
                    params.append(value + " 23:59:59")  # End of the day
                elif value:
                    filter_conditions.append(f"{key} = ?")
                    params.append(value)
            
            if filter_conditions:
                query += " WHERE " + " AND ".join(filter_conditions)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result['count'] if result else 0

    def get_breach_counts(self, filters=None):
        """Get count of breaches by payload and metric type with optional date filtering."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
        SELECT scid, metric_type, COUNT(*) as count
        FROM metric_triggers
        WHERE status = 'BREACH'
        '''
        params = []
        
        # Apply date filters if provided
        if filters:
            date_conditions = []
            if filters.get('date_from'):
                date_conditions.append("timestamp >= ?")
                params.append(filters['date_from'] + " 00:00:00")
            if filters.get('date_to'):
                date_conditions.append("timestamp <= ?")
                params.append(filters['date_to'] + " 23:59:59")
            
            if date_conditions:
                query += " AND " + " AND ".join(date_conditions)
        
        query += " GROUP BY scid, metric_type"
        
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_latest_statuses(self, filters=None):
        """Get the latest status for each payload and metric type with optional date filtering."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create a subquery to get the max timestamp for each (scid, metric_type) pair within the date range
        date_filter = ""
        params = []
        
        if filters and (filters.get('date_from') or filters.get('date_to')):
            date_conditions = []
            if filters.get('date_from'):
                date_conditions.append("timestamp >= ?")
                params.append(filters['date_from'] + " 00:00:00")
            if filters.get('date_to'):
                date_conditions.append("timestamp <= ?")
                params.append(filters['date_to'] + " 23:59:59")
            
            if date_conditions:
                date_filter = " WHERE " + " AND ".join(date_conditions)
        
        # Using a more efficient query approach
        query = f'''
        SELECT t1.scid, t1.metric_type, t1.status
        FROM metric_triggers t1
        INNER JOIN (
            SELECT scid, metric_type, MAX(timestamp) as max_timestamp
            FROM metric_triggers
            {date_filter}
            GROUP BY scid, metric_type
        ) t2 ON t1.scid = t2.scid AND t1.metric_type = t2.metric_type AND t1.timestamp = t2.max_timestamp
        '''
        
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_breach_history(self, scid, metric_type, date_from, date_to):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DATE(timestamp) as day, COUNT(*) as count
            FROM metric_triggers
            WHERE scid=? AND metric_type=? AND status='BREACH'
              AND timestamp >= ? AND timestamp <= ?
            GROUP BY day
            ORDER BY day
        ''', (scid, metric_type, date_from + " 00:00:00", date_to + " 23:59:59"))
        # Fill in days with 0 if no breaches
        start = datetime.strptime(date_from, "%Y-%m-%d")
        end = datetime.strptime(date_to, "%Y-%m-%d")
        day_counts = {row['day']: row['count'] for row in cursor.fetchall()}
        days = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end-start).days+1)]
        return [{'day': d, 'count': day_counts.get(d, 0)} for d in days]

    def close(self):
        """Close the database connection."""
        if hasattr(self.local, 'conn') and self.local.conn:
            self.local.conn.close()
            self.local.conn = None 