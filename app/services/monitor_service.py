from datetime import datetime
from app.database import get_db
from app.models.event import Event
from app.utils import get_logger
from app.config import Config

# Initialize logger
logger = get_logger('services.monitor')
config = Config()

class MonitorService:
    """Service for handling monitoring and threshold checking."""
    
    def __init__(self):
        self.db = get_db()
    
    def check_metrics(self, metrics_data):
        """Check metrics against thresholds and log events."""
        try:
            events = []
            
            for metric_data in metrics_data:
                # Make sure scid is an integer
                try:
                    scid = int(metric_data.get('scid'))
                    metric_data['scid'] = scid  # Update the dict with integer value
                except (ValueError, TypeError):
                    scid = metric_data.get('scid')
                
                metric_type = metric_data.get('metric_type')
                value = metric_data.get('value')
                
                if not all([scid, metric_type, value]):
                    logger.warning(f"Missing required metric data: {metric_data}")
                    continue
                
                # Get threshold from config
                threshold = config.get_threshold(metric_type)
                if threshold is None:
                    logger.warning(f"No threshold configured for metric type: {metric_type}")
                    continue
                
                # Determine status
                status = 'BREACH' if value > threshold else 'NORMAL'
                
                # Create event
                event = Event(
                    scid=scid,
                    metric_type=metric_type,
                    timestamp=datetime.utcnow(),
                    value=value,
                    threshold=threshold,
                    status=status
                )
                
                # Save event to database
                with self.db.get_session() as session:
                    session.add(event)
                    session.commit()
                
                events.append(event)
                logger.info(f"Logged {status} event for SCID {scid}, {metric_type}: {value} > {threshold}")
            
            return events
        except Exception as e:
            logger.error(f"Error checking metrics: {str(e)}", exc_info=True)
            raise
    
    def get_current_status(self, filters=None):
        """Get current status for all payloads and metrics."""
        try:
            # Get latest statuses from database
            latest_statuses = self.db.get_latest_statuses(filters=filters)
            logger.info(f"Found {len(latest_statuses)} latest statuses")
            
            # Get all payloads and metrics from config
            payloads = config.get_payloads()
            metrics = config.get_metrics()
            
            logger.info(f"Config loaded: {len(payloads)} payloads and {len(metrics)} metrics")
            
            # Create status matrix
            status_matrix = {}
            for payload in payloads:
                scid = payload['scid']
                status_matrix[scid] = {
                    'name': payload['name'],
                    'metrics': {}
                }
                
                # Initialize all metrics as NORMAL
                for metric_name, metric_config in metrics.items():
                    threshold = metric_config.get('threshold', 0)
                    status_matrix[scid]['metrics'][metric_name] = {
                        'status': 'NORMAL',
                        'threshold': threshold,
                        'count': 0
                    }
                    logger.debug(f"Initialized metric {metric_name} for payload {scid} with threshold {threshold}")
            
            # Log the set of SCIDs and metric types available in the status matrix
            scids_in_matrix = set(status_matrix.keys())
            metric_types_in_matrix = set()
            for payload_data in status_matrix.values():
                metric_types_in_matrix.update(payload_data['metrics'].keys())
            
            logger.info(f"Status matrix initialized with SCIDs: {scids_in_matrix}")
            logger.info(f"Status matrix initialized with metric types: {metric_types_in_matrix}")
            
            # Update status matrix with latest statuses
            for status in latest_statuses:
                scid = status.scid
                metric_type = status.metric_type
                
                # Convert to int if the scid is numeric 
                # (sometimes the database might return it as a string)
                try:
                    scid = int(scid)
                except (ValueError, TypeError):
                    pass
                    
                if scid in status_matrix and metric_type in status_matrix[scid]['metrics']:
                    status_matrix[scid]['metrics'][metric_type]['status'] = status.status
                    logger.debug(f"Updated status for {scid} {metric_type}: {status.status}")
                else:
                    logger.warning(f"SCID {scid} or metric {metric_type} not found in status matrix")
            
            # Get breach counts
            breach_counts = self.db.get_breach_counts(filters=filters)
            logger.info(f"Found {len(breach_counts)} breach count records")
            
            # Log all breach counts for debugging
            for breach in breach_counts:
                logger.info(f"Breach count: SCID {breach.scid}, metric {breach.metric_type}, count {breach.count}")
            
            # Update breach counts in status matrix
            for breach in breach_counts:
                scid = breach.scid
                metric_type = breach.metric_type
                count = breach.count
                
                # Convert to int if the scid is numeric
                try:
                    scid = int(scid)
                except (ValueError, TypeError):
                    pass
                    
                if scid in status_matrix and metric_type in status_matrix[scid]['metrics']:
                    status_matrix[scid]['metrics'][metric_type]['count'] = count
                    # If there are breaches, ensure the status is set to BREACH
                    if count > 0:
                        status_matrix[scid]['metrics'][metric_type]['status'] = 'BREACH'
                    logger.debug(f"Updated breach count for {scid} {metric_type}: {count}")
                else:
                    logger.warning(f"For breach count: SCID {scid} or metric {metric_type} not found in status matrix")
            
            return status_matrix
        except Exception as e:
            logger.error(f"Error getting current status: {str(e)}", exc_info=True)
            raise

# Create a singleton instance
monitor_service = MonitorService()

def get_monitor_service():
    """Get the singleton monitor service instance."""
    return monitor_service 