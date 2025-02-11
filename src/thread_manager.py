import streamlit as st
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, Any
import threading
from functools import wraps

class ThreadManager:
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers

    def _wrap_with_context(self, func: Callable) -> Callable:
        """Wrap a function to maintain Streamlit's script run context"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the current script run context
            ctx = st.runtime.get_instance()._get_script_run_ctx()
            def run_with_context():
                # Set the context for this thread
                st.runtime.get_instance()._set_script_run_ctx(ctx)
                return func(*args, **kwargs)
            return run_with_context()
        return wrapper

    def process_tasks(self, tasks: List[Callable]) -> List[Any]:
        """Process tasks while maintaining Streamlit's context"""
        wrapped_tasks = [self._wrap_with_context(task) for task in tasks]
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(lambda t: t(), wrapped_tasks))

        return [r for r in results if r is not None]
