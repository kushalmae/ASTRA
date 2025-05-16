import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
import datetime
import sqlalchemy

from app.config import Config
from app.database.base import Base
from app.utils import get_logger

# Initialize logger
logger = get_logger('database')

class Database:
    """Database connection and session management."""
    
    def __init__(self, db_path=None):
        """Initialize database connection.
        
        Args:
            db_path (str, optional): Path to the database file. If not provided,
                                   will use the path from Config.
        """
        self.config = Config()
        self.db_path = db_path or self.config.get_database_path()
        self.engine = None
        self.session_factory = None
        self.Session = None
    
    def init_app(self):
        """Initialize database connection."""
        try:
            # Ensure database directory exists
            db_dir = os.path.dirname(self.db_path)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
            
            # Create engine
            self.engine = create_engine(f'sqlite:///{self.db_path}')
            
            # Create session factory
            self.session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(self.session_factory)
            
            # Create tables
            Base.metadata.create_all(self.engine)
            
            logger.info("Database initialized successfully")
            
        except SQLAlchemyError as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    def get_session(self):
        """Get a new database session."""
        if not self.Session:
            raise RuntimeError("Database not initialized. Call init_app() first.")
        return self.Session()
    
    def close_session(self):
        """Close the current session."""
        if self.Session:
            self.Session.remove()
    
    def cleanup(self):
        """Cleanup database resources."""
        if self.engine:
            self.engine.dispose()
        if self.Session:
            self.Session.remove()
    
    def get_all_triggers(self, limit=25, offset=0, sort_by="timestamp", sort_order="DESC", filters=None):
        """Get all trigger events with optional filtering and sorting."""
        try:
            # Import Event model here to avoid circular imports
            from app.models.event import Event
            
            with self.get_session() as session:
                query = session.query(Event)
                
                # Apply filters
                if filters:
                    if filters.get('scid'):
                        query = query.filter(Event.scid == filters['scid'])
                    if filters.get('metric_type'):
                        query = query.filter(Event.metric_type == filters['metric_type'])
                    if filters.get('status'):
                        query = query.filter(Event.status == filters['status'])
                    if filters.get('date_from'):
                        date_from = datetime.datetime.strptime(filters['date_from'], '%Y-%m-%d')
                        query = query.filter(Event.timestamp >= date_from)
                    if filters.get('date_to'):
                        date_to = datetime.datetime.strptime(filters['date_to'], '%Y-%m-%d')
                        query = query.filter(Event.timestamp < date_to)
                
                # Apply sorting
                sort_column = getattr(Event, sort_by)
                if sort_order.upper() == 'DESC':
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
                
                # Apply pagination
                query = query.limit(limit).offset(offset)
                
                return query.all()
        except Exception as e:
            logger.error(f"Error fetching triggers: {str(e)}", exc_info=True)
            raise
    
    def get_trigger_count(self, filters=None):
        """Get the total count of triggers with optional filtering."""
        try:
            # Import Event model here to avoid circular imports
            from app.models.event import Event
            
            with self.get_session() as session:
                query = session.query(Event)
                
                # Apply filters
                if filters:
                    if filters.get('scid'):
                        query = query.filter(Event.scid == filters['scid'])
                    if filters.get('metric_type'):
                        query = query.filter(Event.metric_type == filters['metric_type'])
                    if filters.get('status'):
                        query = query.filter(Event.status == filters['status'])
                    if filters.get('date_from'):
                        date_from = datetime.datetime.strptime(filters['date_from'], '%Y-%m-%d')
                        query = query.filter(Event.timestamp >= date_from)
                    if filters.get('date_to'):
                        date_to = datetime.datetime.strptime(filters['date_to'], '%Y-%m-%d')
                        query = query.filter(Event.timestamp < date_to)
                
                return query.count()
        except Exception as e:
            logger.error(f"Error counting triggers: {str(e)}", exc_info=True)
            raise
    
    def get_breach_counts(self, filters=None):
        """Get count of breaches by payload and metric type."""
        try:
            # Import Event model here to avoid circular imports
            from app.models.event import Event
            
            with self.get_session() as session:
                # Convert scid to integer for proper key matching with status_matrix
                query = session.query(
                    Event.scid.cast(type_=sqlalchemy.Integer).label('scid'),  # Cast to integer
                    Event.metric_type,
                    func.count(Event.id).label('count')
                ).filter(Event.status == 'BREACH')
                
                # Apply date filters
                if filters:
                    if filters.get('date_from'):
                        date_from = datetime.datetime.strptime(filters['date_from'], '%Y-%m-%d')
                        query = query.filter(Event.timestamp >= date_from)
                    if filters.get('date_to'):
                        date_to = datetime.datetime.strptime(filters['date_to'], '%Y-%m-%d')
                        query = query.filter(Event.timestamp < date_to)
                
                query = query.group_by(Event.scid, Event.metric_type)
                
                # Execute query and convert results to list of named tuples
                results = query.all()
                logger.info(f"Found {len(results)} breach count results")
                
                return results
        except Exception as e:
            logger.error(f"Error getting breach counts: {str(e)}", exc_info=True)
            raise
    
    def get_latest_statuses(self, filters=None):
        """Get the latest status for each payload and metric."""
        try:
            # Import Event model here to avoid circular imports
            from app.models.event import Event
            
            with self.get_session() as session:
                # Subquery to get the latest timestamp for each scid and metric_type
                latest_timestamps = session.query(
                    Event.scid.cast(type_=sqlalchemy.Integer).label('scid'),  # Cast to integer
                    Event.metric_type,
                    func.max(Event.timestamp).label('max_timestamp')
                ).group_by(Event.scid, Event.metric_type).subquery()
                
                # Main query to get the latest status
                query = session.query(Event).join(
                    latest_timestamps,
                    (Event.scid == latest_timestamps.c.scid) &
                    (Event.metric_type == latest_timestamps.c.metric_type) &
                    (Event.timestamp == latest_timestamps.c.max_timestamp)
                )
                
                # Apply date filters
                if filters:
                    if filters.get('date_from'):
                        date_from = datetime.datetime.strptime(filters['date_from'], '%Y-%m-%d')
                        query = query.filter(Event.timestamp >= date_from)
                    if filters.get('date_to'):
                        date_to = datetime.datetime.strptime(filters['date_to'], '%Y-%m-%d')
                        query = query.filter(Event.timestamp < date_to)
                
                events = query.all()
                
                # Ensure scid is an integer where possible
                for event in events:
                    try:
                        event.scid = int(event.scid)
                    except (ValueError, TypeError):
                        # Keep as is if not convertible
                        pass
                
                return events
        except Exception as e:
            logger.error(f"Error getting latest statuses: {str(e)}", exc_info=True)
            raise
    
    def log_trigger(self, scid, metric_type, timestamp, value, threshold, status):
        """Log a trigger event to the database.
        
        Args:
            scid (str): Spacecraft ID
            metric_type (str): Type of metric
            timestamp (datetime): Event timestamp
            value (float): Metric value
            threshold (float): Threshold value
            status (str): Event status
        """
        try:
            # Import Event model here to avoid circular imports
            from app.models.event import Event
            
            with self.get_session() as session:
                event = Event(
                    scid=scid,
                    metric_type=metric_type,
                    timestamp=timestamp,
                    value=value,
                    threshold=threshold,
                    status=status
                )
                session.add(event)
                session.commit()
                
                # If this is a breach, also log to breach history
                if status == 'BREACH':
                    from app.models.event import BreachHistory
                    breach = BreachHistory(
                        event_id=event.id,
                        scid=scid,
                        metric_type=metric_type,
                        value=value,
                        threshold=threshold,
                        timestamp=timestamp
                    )
                    session.add(breach)
                    session.commit()
                
                logger.info(f"Logged trigger: {scid} {metric_type} {status}")
        except Exception as e:
            logger.error(f"Error logging trigger: {str(e)}", exc_info=True)
            raise

# Create a singleton instance
db = Database()

def get_db():
    """Get the singleton database instance."""
    return db 