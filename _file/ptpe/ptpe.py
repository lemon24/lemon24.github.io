import queue, time
import atexit
import threading
import multiprocessing
import concurrent.futures


class ProcessThreadPoolExecutor(concurrent.futures.ProcessPoolExecutor):

    def __init__(self, max_threads=None, initializer=None, initargs=()):
        self.__result_queue = multiprocessing.Queue()
        super().__init__(
            initializer=_init_process,
            initargs=(self.__result_queue, max_threads, initializer, initargs)
        )
        self.__tasks = {}
        self.__result_handler = threading.Thread(target=self.__handle_results)
        self.__result_handler.start()

    def submit(self, fn, *args, **kwargs):
        outer = concurrent.futures.Future()
        task_id = id(outer)
        self.__tasks[task_id] = outer

        outer.set_running_or_notify_cancel()
        inner = super().submit(_submit, task_id, fn, *args, **kwargs)
        inner.task_id = task_id
        inner.add_done_callback(self.__handle_inner)

        return outer

    def __handle_inner(self, inner):
        task_id = inner.task_id
        if exception := inner.exception():
            if outer := self.__tasks.pop(task_id, None):
                outer.set_exception(exception)

    def __handle_results(self):
        last_broken_check = time.monotonic()

        while True:
            now = time.monotonic()
            if now - last_broken_check >= .1:
                if exc := self.__check_broken():
                    break
                last_broken_check = now

            try:
                value = self.__result_queue.get(timeout=.1)
            except queue.Empty:
                continue

            if not value:
                return

            task_id, ok, result = value
            if outer := self.__tasks.pop(task_id, None):
                if ok:
                    outer.set_result(result)
                else:
                    outer.set_exception(result)

        while self.__tasks:
            try:
                _, outer = self.__tasks.popitem()
            except KeyError:
                break
            outer.set_exception(exc)

    def __check_broken(self):
        try:
            super().submit(int).cancel()
        except concurrent.futures.BrokenExecutor as e:
            return type(e)(str(e))
        except RuntimeError as e:
            if 'shutdown' not in str(e):
                raise
        return None

    def shutdown(self, wait=True):
        super().shutdown(wait=wait)
        if self.__result_queue:
            self.__result_queue.put(None)
            if wait:
                self.__result_handler.join()
            self.__result_queue.close()
            self.__result_queue = None


_executor = None
_result_queue = None

def _init_process(queue, max_threads, initializer, initargs):
    global _executor, _result_queue

    _executor = concurrent.futures.ThreadPoolExecutor(max_threads)
    atexit.register(_executor.shutdown)

    _result_queue = queue
    atexit.register(_result_queue.close)

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
    with ProcessThreadPoolExecutor() as e:
        print(list(e.map(_do_stuff, [0, 1, 2])))
