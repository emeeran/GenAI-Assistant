import time
from functools import wraps
import streamlit as st
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        if not hasattr(st.session_state, "performance_metrics"):
            st.session_state.performance_metrics = []

    def measure(self, func_name: str) -> None:
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self._log_metric(func_name, duration, "success")
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self._log_metric(func_name, duration, "error", str(e))
                    raise
            return wrapper
        return decorator

    def _log_metric(self, name: str, duration: float, status: str, error: str = None):
        metric = {
            "name": name,
            "duration": duration,
            "timestamp": time.time(),
            "status": status
        }
        if error:
            metric["error"] = error
        st.session_state.performance_metrics.append(metric)

    def get_metrics(self) -> List[Dict[str, Any]]:
        return st.session_state.performance_metrics

    def render_metrics(self):
        if not st.session_state.performance_metrics:
            return

        with st.expander("Performance Metrics", expanded=False):
            metrics_df = pd.DataFrame(st.session_state.performance_metrics)
            st.dataframe(
                metrics_df[["name", "duration", "status"]].tail(10),
                use_container_width=True
            )
