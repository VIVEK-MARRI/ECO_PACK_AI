"""
Online Learning Feedback System
Real-time feedback collection and event streaming
"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import structlog
from abc import ABC, abstractmethod

logger = structlog.get_logger(__name__)


class FeedbackEventType(Enum):
    """Event types in the feedback loop"""
    PREDICTION_MADE = "prediction_made"
    OUTCOME_OBSERVED = "outcome_observed"
    DAMAGE_REPORTED = "damage_reported"
    COST_CONFIRMED = "cost_confirmed"
    RETRAINING_TRIGGERED = "retraining_triggered"
    MODEL_DEPLOYED = "model_deployed"
    DRIFT_DETECTED = "drift_detected"


@dataclass
class FeedbackEvent:
    """Feedback event schema"""
    event_id: str
    event_type: FeedbackEventType
    timestamp: datetime
    product_id: str
    packaging_id: str
    
    # Prediction data
    predicted_cost: Optional[float] = None
    predicted_co2: Optional[float] = None
    predicted_damage_prob: Optional[float] = None
    
    # Actual outcome
    actual_cost: Optional[float] = None
    actual_co2: Optional[float] = None
    actual_damage_prob: Optional[float] = None
    damage_severity: Optional[str] = None  # none, minor, moderate, severe
    
    # Metadata
    user_id: Optional[str] = None
    warehouse_location: Optional[str] = None
    season: Optional[str] = None
    
    # Additional context
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict())


class EventQueue(ABC):
    """Abstract interface for event queue"""
    
    @abstractmethod
    def publish(self, event: FeedbackEvent) -> bool:
        """Publish event to queue"""
        pass
    
    @abstractmethod
    def consume(self, batch_size: int = 100) -> List[FeedbackEvent]:
        """Consume events from queue"""
        pass
    
    @abstractmethod
    def get_queue_size(self) -> int:
        """Get number of events in queue"""
        pass


class InMemoryEventQueue(EventQueue):
    """In-memory event queue (for testing/local development)"""
    
    def __init__(self, max_size: int = 100000):
        self.queue: List[FeedbackEvent] = []
        self.max_size = max_size
        self.published_count = 0
    
    def publish(self, event: FeedbackEvent) -> bool:
        """Publish event"""
        if len(self.queue) >= self.max_size:
            logger.warning("Event queue at capacity, dropping oldest event")
            self.queue.pop(0)
        
        self.queue.append(event)
        self.published_count += 1
        
        logger.info(
            "Event published",
            event_type=event.event_type.value,
            event_id=event.event_id,
            queue_size=len(self.queue)
        )
        
        return True
    
    def consume(self, batch_size: int = 100) -> List[FeedbackEvent]:
        """Consume events"""
        batch = self.queue[:batch_size]
        self.queue = self.queue[batch_size:]
        return batch
    
    def get_queue_size(self) -> int:
        """Get queue size"""
        return len(self.queue)


class KafkaEventQueue(EventQueue):
    """Kafka event queue (for production)"""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092", topic: str = "eco-pack-ai-feedback"):
        """
        Initialize Kafka event queue
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Topic name for feedback events
        """
        try:
            from kafka import KafkaProducer, KafkaConsumer
            self.KafkaProducer = KafkaProducer
            self.KafkaConsumer = KafkaConsumer
        except ImportError:
            logger.warning("kafka-python not installed, falling back to in-memory queue")
            self.producer = None
            self.consumer = None
        
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = None
        self.consumer = None
        
        self._initialize_producers()
    
    def _initialize_producers(self):
        """Initialize Kafka producer/consumer"""
        try:
            self.producer = self.KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: v.to_json().encode('utf-8')
            )
            logger.info("Kafka producer initialized", topic=self.topic)
        except Exception as e:
            logger.error("Failed to initialize Kafka producer", error=str(e))
    
    def publish(self, event: FeedbackEvent) -> bool:
        """Publish event to Kafka"""
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False
        
        try:
            future = self.producer.send(self.topic, value=event)
            record_metadata = future.get(timeout=10)
            
            logger.info(
                "Event published to Kafka",
                topic=record_metadata.topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset
            )
            return True
        
        except Exception as e:
            logger.error("Failed to publish event to Kafka", error=str(e))
            return False
    
    def consume(self, batch_size: int = 100) -> List[FeedbackEvent]:
        """Consume events from Kafka"""
        if not self.consumer:
            logger.error("Kafka consumer not initialized")
            return []
        
        try:
            messages = []
            for _ in range(batch_size):
                msg = self.consumer.poll(timeout_ms=1000)
                if msg:
                    messages.append(msg)
            
            return messages
        
        except Exception as e:
            logger.error("Failed to consume from Kafka", error=str(e))
            return []
    
    def get_queue_size(self) -> int:
        """Estimate queue size (Kafka limitation)"""
        # In production, would query __consumer_offsets topic
        return -1  # Unknown


class FeedbackCollector:
    """
    Collects feedback from packaging decisions.
    Central hub for feedback pipeline.
    """
    
    def __init__(self, event_queue: EventQueue = None):
        """
        Initialize feedback collector
        
        Args:
            event_queue: Event queue implementation (defaults to in-memory)
        """
        self.event_queue = event_queue or InMemoryEventQueue()
        self.prediction_cache: Dict[str, FeedbackEvent] = {}
        
        logger.info("FeedbackCollector initialized")
    
    def record_prediction(
        self,
        product_id: str,
        packaging_id: str,
        predicted_cost: float,
        predicted_co2: float,
        predicted_damage_prob: float,
        user_id: Optional[str] = None,
        warehouse_location: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Record a packaging prediction
        
        Args:
            product_id: Product identifier
            packaging_id: Packaging option identifier
            predicted_cost: Predicted cost
            predicted_co2: Predicted CO2
            predicted_damage_prob: Predicted damage probability
            user_id: User identifier
            warehouse_location: Warehouse location
            metadata: Additional metadata
        
        Returns:
            Event ID for tracking
        """
        event_id = str(uuid.uuid4())
        
        event = FeedbackEvent(
            event_id=event_id,
            event_type=FeedbackEventType.PREDICTION_MADE,
            timestamp=datetime.utcnow(),
            product_id=product_id,
            packaging_id=packaging_id,
            predicted_cost=predicted_cost,
            predicted_co2=predicted_co2,
            predicted_damage_prob=predicted_damage_prob,
            user_id=user_id,
            warehouse_location=warehouse_location,
            metadata=metadata
        )
        
        # Cache for later outcome matching
        self.prediction_cache[event_id] = event
        
        # Publish to event queue
        self.event_queue.publish(event)
        
        logger.info(
            "Prediction recorded",
            event_id=event_id,
            product_id=product_id,
            packaging_id=packaging_id
        )
        
        return event_id
    
    def record_outcome(
        self,
        event_id: str,
        actual_cost: Optional[float] = None,
        actual_co2: Optional[float] = None,
        actual_damage_prob: Optional[float] = None,
        damage_severity: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Record actual outcome of a prediction
        
        Args:
            event_id: Original prediction event ID
            actual_cost: Actual cost
            actual_co2: Actual CO2
            actual_damage_prob: Actual damage
            damage_severity: Damage severity level
            metadata: Additional metadata
        
        Returns:
            Success status
        """
        if event_id not in self.prediction_cache:
            logger.warning("Outcome recorded for unknown prediction", event_id=event_id)
        
        # Get original prediction or create new event
        if event_id in self.prediction_cache:
            original_event = self.prediction_cache[event_id]
            event = FeedbackEvent(
                event_id=event_id,
                event_type=FeedbackEventType.OUTCOME_OBSERVED,
                timestamp=datetime.utcnow(),
                product_id=original_event.product_id,
                packaging_id=original_event.packaging_id,
                predicted_cost=original_event.predicted_cost,
                predicted_co2=original_event.predicted_co2,
                predicted_damage_prob=original_event.predicted_damage_prob,
                actual_cost=actual_cost,
                actual_co2=actual_co2,
                actual_damage_prob=actual_damage_prob,
                damage_severity=damage_severity,
                user_id=original_event.user_id,
                warehouse_location=original_event.warehouse_location,
                metadata=metadata
            )
            
            # Remove from cache
            del self.prediction_cache[event_id]
        else:
            event = FeedbackEvent(
                event_id=event_id,
                event_type=FeedbackEventType.OUTCOME_OBSERVED,
                timestamp=datetime.utcnow(),
                product_id="unknown",
                packaging_id="unknown",
                actual_cost=actual_cost,
                actual_co2=actual_co2,
                actual_damage_prob=actual_damage_prob,
                damage_severity=damage_severity,
                metadata=metadata
            )
        
        # Publish outcome
        self.event_queue.publish(event)
        
        # Calculate prediction error
        error_metrics = {}
        if event.predicted_cost and event.actual_cost:
            error_metrics['cost_error_pct'] = abs(
                (event.predicted_cost - event.actual_cost) / event.actual_cost
            ) * 100
        if event.predicted_co2 and event.actual_co2:
            error_metrics['co2_error_pct'] = abs(
                (event.predicted_co2 - event.actual_co2) / event.actual_co2
            ) * 100
        
        logger.info(
            "Outcome recorded",
            event_id=event_id,
            damage_severity=damage_severity,
            **error_metrics
        )
        
        return True
    
    def get_pending_events(self, batch_size: int = 100) -> List[FeedbackEvent]:
        """Get pending feedback events for retraining"""
        return self.event_queue.consume(batch_size)
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        queue_size = self.event_queue.get_queue_size()
        
        return {
            'queue_size': queue_size,
            'cached_predictions': len(self.prediction_cache),
            'queue_type': self.event_queue.__class__.__name__
        }
    
    def batch_record_outcomes(
        self,
        outcomes: List[Dict[str, Any]]
    ) -> int:
        """
        Batch record multiple outcomes
        
        Args:
            outcomes: List of outcome dictionaries
        
        Returns:
            Number of successfully recorded outcomes
        """
        count = 0
        
        for outcome in outcomes:
            try:
                self.record_outcome(
                    event_id=outcome.get('event_id'),
                    actual_cost=outcome.get('actual_cost'),
                    actual_co2=outcome.get('actual_co2'),
                    actual_damage_prob=outcome.get('actual_damage_prob'),
                    damage_severity=outcome.get('damage_severity'),
                    metadata=outcome.get('metadata')
                )
                count += 1
            except Exception as e:
                logger.error("Failed to record outcome", error=str(e))
        
        return count
