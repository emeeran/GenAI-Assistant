import streamlit as st
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, List
import threading
import warnings

try:
    from streamlit.runtime.scriptrunner.script_run_context import (
        get_script_run_ctx,
        add_script_run_ctx,
    )
except ImportError:
    # Fallback: define no-op functions if context is unavailable
    def get_script_run_ctx():
        return None

    def add_script_run_ctx(thread, ctx):
        pass


def with_script_run_context(fn: Callable) -> Callable:
    ctx = get_script_run_ctx()  # capture current context (could be None)

    def wrapped(*args, **kwargs):
        # Suppress missing ScriptRunContext warnings in worker threads.
        warnings.filterwarnings("ignore", message=".*missing ScriptRunContext.*")
        if ctx is not None:
            add_script_run_ctx(threading.current_thread(), ctx)
        return fn(*args, **kwargs)

    return wrapped


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

    def submit_task(self, fn: Callable, *args, **kwargs) -> Future:
        self._ensure_executor()
        wrapped_fn = with_script_run_context(fn)
        return st.session_state._executor.submit(wrapped_fn, *args, **kwargs)

    def process_tasks(self, tasks: List[Callable], *args) -> List[Any]:
        futures = [self.submit_task(task, *args) for task in tasks]
        results = []
        for future in futures:
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                st.error(f"Task error: {e}")
        return results
