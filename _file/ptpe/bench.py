import time
import threading
from contextlib import contextmanager

try:
    import psutil
except ImportError:
    pass


class Client:
    io_time = 0.02
    cpu_time = 0.0008

    def method(self, arg):
        # simulate I/O
        time.sleep(self.io_time)

        # simulate CPU-bound work
        start = time.perf_counter()
        while time.perf_counter() - start < self.cpu_time:
            for i in range(100): i ** i

        return arg


# this code runs in each worker process

client = None

def init_client(*args):
    global client
    client = Client(*args)

def do_stuff(*args):
    return client.method(*args)


@contextmanager
def timer():
    start = time.perf_counter()
    yield
    end = time.perf_counter()
    print(f"elapsed: {end-start:1.3f}")


def benchmark(executor, n=10_000, timer=timer, chunksize=10):
    with executor:
        # make sure all the workers are started,
        # so we don't measure their startup time
        list(executor.map(time.sleep, [0] * 200))

        with timer():
            values = list(executor.map(do_stuff, range(n), chunksize=chunksize))

        assert values == list(range(n)), values


@contextmanager
def top():
    """Print information about current and child processes.

    RES is the resident set size. USS is the unique set size.
    %CPU is the CPU utilization. nTH is the number of threads.

    """
    process = psutil.Process()
    processes = [process] + process.children(True)
    for p in processes: p.cpu_percent()

    yield

    print(f"{'PID':>7} {'RES':>7} {'USS':>7} {'%CPU':>7} {'nTH':>7}")
    for p in processes:
        try:
            m = p.memory_full_info()
        except psutil.AccessDenied:
            m = p.memory_info()
        rss = m.rss / 2**20
        uss = getattr(m, 'uss', 0) / 2**20
        cpu = p.cpu_percent()
        nth = p.num_threads()
        print(f"{p.pid:>7} {rss:6.1f}m {uss:6.1f}m {cpu:7.1f} {nth:>7}")


@contextmanager
def terminate_child(interval=1):
    threading.Timer(interval, psutil.Process().children()[-1].terminate).start()
    yield


from ptpe import ProcessThreadPoolExecutor


def debug_shutdown(cls=ProcessThreadPoolExecutor):
    """ python -c 'from bench import *; debug_shutdown()' """
    with cls(2) as executor:
        executor.submit(_sleep, 2)
        time.sleep(1)
        print('before shut down')
        executor.shutdown()
        print('after shut down')
    print('after with')

def _sleep(n):
    print('sleeping', n)
    time.sleep(n)
    print('slept', n)


def debug_kill(kill_interval=1, print_interval=.5, cls=ProcessThreadPoolExecutor):
    """ python -c 'from bench import *; debug_kill(1) """
    print('starting')
    executor = cls(2, initializer=init_client)

    def print_debug():
        print(
            f"len(tasks)={len(executor._ProcessThreadPoolExecutor__tasks)} "
            f"PPE.broken={executor._broken} "
        )
        if executor._broken:
            return
        threading.Timer(print_interval, print_debug).start()

    print_debug()
    benchmark(executor, timer=lambda: terminate_child(kill_interval))
    print('done')


lines = """\
# benchmark(ProcessThreadPoolExecutor(10, initializer=init_client))
# benchmark(ProcessThreadPoolExecutor(20, initializer=init_client))
benchmark(ProcessThreadPoolExecutor(30, initializer=init_client))
benchmark(ProcessThreadPoolExecutor(40, initializer=init_client))

init_client()
# benchmark(ThreadPoolExecutor(10))
# benchmark(ThreadPoolExecutor(20))
# benchmark(ThreadPoolExecutor(30))
benchmark(ThreadPoolExecutor(40))

# benchmark(ProcessPoolExecutor(10, initializer=init_client))
# benchmark(ProcessPoolExecutor(20, initializer=init_client))
# benchmark(ProcessPoolExecutor(30, initializer=init_client))
benchmark(ProcessPoolExecutor(40, initializer=init_client))

""".splitlines()


if __name__ == '__main__':
    import sys
    from concurrent.futures import *

    def repl_eval(expr):
        expr = expr.strip()
        if not expr or expr.startswith('#'):
            return
        print(f">>> {expr}")
        rv = eval(expr)
        if rv is not None:
            print(rv)

    if not sys.flags.interactive:
        for line in lines:
            repl_eval(line)
