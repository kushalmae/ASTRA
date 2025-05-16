from datetime import datetime, timedelta
from sqlalchemy import func, and_
from app.database import get_db
from app.models.event import Event
from app.utils import get_logger
from app.config import cache

# Initialize logger
logger = get_logger('services.event')

class EventService:
    """Service for handling event-related business logic."""
    
    def __init__(self):
        self.db = get_db()
    
    @cache.memoize(timeout=300)
    def get_events(self, page=1, page_size=25, sort_by="timestamp", sort_order="DESC", filters=None):
        """Get paginated events with filtering and sorting."""
        try:
            # Validate and normalize filters
            normalized_filters = self._normalize_filters(filters)
            
            # Get events from database with optimized query
            with self.db.get_session() as session:
                # Build base query
                query = session.query(Event)
                
                # Apply filters efficiently
                if normalized_filters:
                    conditions = []
                    if normalized_filters.get('scid'):
                        conditions.append(Event.scid == normalized_filters['scid'])
                    if normalized_filters.get('metric_type'):
                        conditions.append(Event.metric_type == normalized_filters['metric_type'])
                    if normalized_filters.get('status'):
                        conditions.append(Event.status == normalized_filters['status'])
                    if normalized_filters.get('date_from'):
                        conditions.append(Event.timestamp >= normalized_filters['date_from'])
                    if normalized_filters.get('date_to'):
                        conditions.append(Event.timestamp <= normalized_filters['date_to'])
                    
                    if conditions:
                        query = query.filter(and_(*conditions))
                
                # Apply sorting using index
                sort_column = getattr(Event, sort_by)
                if sort_order.upper() == 'DESC':
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
                
                # Get total count efficiently
                total_count = query.count()
                
                # Apply pagination
                events = query.limit(page_size).offset((page - 1) * page_size).all()
            
            return {
                'events': [event.to_dict() for event in events],
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size if total_count > 0 else 1
            }
        except Exception as e:
            logger.error(f"Error getting events: {str(e)}", exc_info=True)
            raise
    
    @cache.memoize(timeout=300)
    def get_breach_history(self, scid, metric_type, date_from, date_to):
        """Get breach history for a specific payload and metric."""
        try:
            # Validate dates
            start_date = datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.strptime(date_to, "%Y-%m-%d")
            
            if end_date < start_date:
                raise ValueError("End date cannot be before start date")
            
            # Get all events including values and thresholds for the chart
            with self.db.get_session() as session:
                query = session.query(Event).filter(
                    Event.scid == scid,
                    Event.metric_type == metric_type,
                    Event.status == 'BREACH',  # Only get breach events
                    Event.timestamp >= start_date,
                    Event.timestamp <= end_date + timedelta(days=1)
                ).order_by(Event.timestamp)
                
                breach_events = query.all()
            
            logger.info(f"Found {len(breach_events)} breach events for SCID {scid}, metric {metric_type}")
            
            # Convert events to the format needed for the chart
            history = []
            for event in breach_events:
                history.append({
                    'timestamp': event.timestamp.isoformat(),
                    'value': event.value,
                    'threshold': event.threshold,
                    'status': event.status
                })
            
            if not history:
                logger.warning(f"No breach history found for SCID {scid}, metric {metric_type}")
                # Return empty array if there's no data
                return []
            
            return history
        except Exception as e:
            logger.error(f"Error getting breach history: {str(e)}", exc_info=True)
            raise
    
    def _normalize_filters(self, filters):
        """Normalize and validate filter parameters."""
        if not filters:
            return {}
        
        normalized = {}
        
        # Handle SCID
        if filters.get('scid'):
            try:
                normalized['scid'] = int(filters['scid'])
            except ValueError:
                logger.warning(f"Invalid SCID value: {filters['scid']}")
                raise ValueError("Invalid SCID value")
        
        # Handle metric type
        if filters.get('metric_type'):
            normalized['metric_type'] = filters['metric_type']
        
        # Handle status
        if filters.get('status'):
            if filters['status'] not in ['BREACH', 'NORMAL']:
                logger.warning(f"Invalid status value: {filters['status']}")
                raise ValueError("Invalid status value")
            normalized['status'] = filters['status']
        
        # Handle dates
        if filters.get('date_from'):
            try:
                normalized['date_from'] = datetime.strptime(filters['date_from'], "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Invalid date_from value: {filters['date_from']}")
                raise ValueError("Invalid date_from value")
        
        if filters.get('date_to'):
            try:
                normalized['date_to'] = datetime.strptime(filters['date_to'], "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Invalid date_to value: {filters['date_to']}")
                raise ValueError("Invalid date_to value")
        
        return normalized

# Create a singleton instance
event_service = EventService()

def get_event_service():
    """Get the singleton event service instance."""
    return event_service 