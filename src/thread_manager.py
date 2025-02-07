import streamlit as st
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, List
from queue import Queue


class ThreadManager:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._ensure_executor()

    def _ensure_executor(self):
        if (
            not hasattr(st.session_state, "_executor")
            or st.session_state._executor._shutdown
        ):
            st.session_state._executor = ThreadPoolExecutor(
                max_workers=self.max_workers
            )
            st.session_state._results_queue = Queue()

    def submit_task(self, fn: Callable, *args, **kwargs) -> Future:
        """Submit a task to be executed in the thread pool"""
        self._ensure_executor()
        return st.session_state._executor.submit(fn, *args, **kwargs)

    def process_tasks(self, tasks: List[Callable], *args) -> List[Any]:
        """Process multiple tasks and collect results"""
        futures = [self.submit_task(task, *args) for task in tasks]
        results = []

        # Use main thread to update Streamlit
        for future in futures:
            try:
                result = future.result()
                if result:
                    results.append(result)
                    # Force Streamlit to update
                    st.session_state._results_queue.put(result)
            except Exception as e:
                st.error(f"Task error: {e}")

        return results
