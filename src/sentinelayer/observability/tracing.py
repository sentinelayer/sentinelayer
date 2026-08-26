import uuid
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger("sentinelayer.tracing")

class Tracer:
    def __init__(self):
        self.spans = {}
        self.active_spans = {}
    
    def start_span(self, name: str, parent_id: str = None) -> str:
        span_id = str(uuid.uuid4())
        self.active_spans[span_id] = {
            "id": span_id,
            "name": name,
            "parent_id": parent_id,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "duration_ms": None,
            "metadata": {}
        }
        logger.info(f"Span started: {name} ({span_id})")
        return span_id
    
    def end_span(self, span_id: str, metadata: Dict = None):
        if span_id not in self.active_spans:
            return
        
        span = self.active_spans[span_id]
        end_time = datetime.utcnow()
        start_time = datetime.fromisoformat(span["start_time"])
        span["end_time"] = end_time.isoformat()
        span["duration_ms"] = (end_time - start_time).total_seconds() * 1000
        if metadata:
            span["metadata"] = metadata
        
        self.spans[span_id] = span
        del self.active_spans[span_id]
        logger.info(f"Span ended: {span['name']} ({span['duration_ms']:.2f}ms)")
    
    def get_trace(self, span_id: str) -> Dict:
        if span_id in self.spans:
            return self.spans[span_id]
        if span_id in self.active_spans:
            return self.active_spans[span_id]
        return {"error": "Span not found"}
    
    def get_all_traces(self) -> List[Dict]:
        return list(self.spans.values())

tracer = Tracer()
