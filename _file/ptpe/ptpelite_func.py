import sys
import time
import queue
import itertools
import threading
import multiprocessing
import concurrent.futures
from functools import partial
from contextlib import contextmanager


def init(max_threads=None, initializer=None, initargs=()):
    global _result_queue, _inner, _tasks, _result_handler
    _result_queue = multiprocessing.Queue()
    _inner = concurrent.futures.ProcessPoolExecutor(
        initializer=_init_process,
        initargs=(_result_queue, max_threads, initializer, initargs)
    )
    _tasks = {}
    _result_handler = threading.Thread(target=_handle_results)
    _result_handler.start()

def submit(fn, *args, **kwargs):
    outer = concurrent.futures.Future()
    task_id = id(outer)
    _tasks[task_id] = outer

    outer.set_running_or_notify_cancel()
    inner = _inner.submit(_submit, task_id, fn, *args, **kwargs)

    return outer

def _handle_results():
    for task_id, ok, result in iter(_result_queue.get, None):
        outer = _tasks.pop(task_id)
        if ok:
            outer.set_result(result)
        else:
            outer.set_exception(result)

def shutdown(wait=True):
    global _result_queue
    _inner.shutdown(wait=wait)
    if _result_queue:
        _result_queue.put(None)
        if wait:
            _result_handler.join()
        _result_queue.close()
        _result_queue = None


@contextmanager
def init_cm(*args, **kwargs):
    init(*args, **kwargs)
    try:
        yield sys.modules[__name__]
    finally:
        shutdown()


def _map(fn, *iterables, timeout=None, chunksize=1):
    # concurrent.futures._base.Executor.map

    if timeout is not None:
        end_time = timeout + time.monotonic()

    fs = [submit(fn, *args) for args in zip(*iterables)]

    def result_iterator():
        try:
            fs.reverse()
            while fs:
                if timeout is None:
                    yield _result_or_cancel(fs.pop())
                else:
                    yield _result_or_cancel(fs.pop(), end_time - time.monotonic())
        finally:
            for future in fs:
                future.cancel()
    return result_iterator()

def map(fn, *iterables, timeout=None, chunksize=1):
    # concurrent.futures.process.ProcessPoolExecutor.map

    if chunksize < 1:
        raise ValueError("chunksize must be >= 1.")

    results = _map(partial(_process_chunk, fn),
                   itertools.batched(zip(*iterables), chunksize),
                   timeout=timeout)
    return _chain_from_iterable_of_lists(results)


def _result_or_cancel(fut, timeout=None):
    # concurrent.futures._base._result_or_cancel
    try:
        try:
            return fut.result(timeout)
        finally:
            fut.cancel()
    finally:
        del fut

def _process_chunk(fn, chunk):
    # concurrent.futures.process._process_chunk
    return [fn(*args) for args in chunk]

def _chain_from_iterable_of_lists(iterable):
    # concurrent.futures.process._chain_from_iterable_of_lists
    for element in iterable:
        element.reverse()
        while element:
            yield element.pop()


# this code runs in each worker process

_executor = None
_result_queue = None

def _init_process(queue, max_threads, initializer, initargs):
    global _executor, _result_queue

    _executor = concurrent.futures.ThreadPoolExecutor(max_threads)
    _result_queue = queue

    if initializer:
        initializer(*initargs)

def _submit(task_id, fn, *args, **kwargs):
    task = _executor.submit(fn, *args, **kwargs)
    task.task_id = task_id
    task.add_done_callback(_put_result)

def _put_result(task):
    if exception := task.exception():
        _result_queue.put((task.task_id, False, exception))
    else:
        _result_queue.put((task.task_id, True, task.result()))


def _do_stuff(n):
    print(f"doing: {n}")
    return n ** 2

if __name__ == '__main__':
    # import ptpe
    ptpe = sys.modules[__name__]

    with ptpe.init_cm() as e:
        print(list(e.map(_do_stuff, [0, 1, 2])))
