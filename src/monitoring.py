import time
from functools import wraps
import streamlit as st

def measure_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time

        if not hasattr(st.session_state, 'performance_metrics'):
            st.session_state.performance_metrics = []

        st.session_state.performance_metrics.append({
            'function': func.__name__,
            'duration': duration,
            'timestamp': time.time()
        })

        return result
    return wrapper
