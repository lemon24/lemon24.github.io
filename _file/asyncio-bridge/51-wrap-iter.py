import asyncio
import contextlib
import threading
import sys

import aiohttp


class ThreadRunner:

    def __init__(self, *args, **kwargs):
        self._runner = asyncio.Runner(*args, **kwargs)
        self._thread = None
        self._stack = contextlib.ExitStack()

    def __enter__(self):
        self._lazy_init()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        try:
            self._stack.close()
        finally:
            loop = self.get_loop()
            loop.call_soon_threadsafe(loop.stop)
            self._thread.join()

    def get_loop(self):
        self._lazy_init()
        return self._runner.get_loop()

    def run(self, coro):
        loop = self.get_loop()
        return asyncio.run_coroutine_threadsafe(coro, loop).result()

    def _lazy_init(self):
        if self._thread:
            return

        loop_created = threading.Event()

        def run_forever():
            with self._runner as runner:
                loop = runner.get_loop()
                asyncio.set_event_loop(loop)
                loop_created.set()
                loop.run_forever()

        self._thread = threading.Thread(
            target=run_forever, name='LoopThread', daemon=True
        )
        self._thread.start()
        loop_created.wait()

    @contextlib.contextmanager
    def wrap_context(self, cm=None, factory=None):
        if cm is None:
            cm = self.run(call_async(factory))
        aenter = type(cm).__aenter__
        aexit = type(cm).__aexit__
        value = self.run(aenter(cm))
        try:
            yield value
        except:
            if not self.run(aexit(cm, *sys.exc_info())):
                raise
        else:
            self.run(aexit(cm, None, None, None))

    def enter_context(self, cm=None, factory=None):
        cm = self.wrap_context(cm=cm, factory=factory)
        return self._stack.enter_context(cm)

    def wrap_iter(self, it):
        it = aiter(it)
        while True:
            try:
                yield self.run(anext(it))
            except StopAsyncIteration:
                break


async def call_async(callable):
    return callable()


async def do_stuff(session):
    async with session.get('https://death.andgravity.com/') as response:
        loop = asyncio.get_running_loop()
        thread = threading.current_thread()
        print('got', response.status, 'in loop', id(loop), 'in', thread.name)


def do_stuff_in_threads(run, session, n=1):
    threads = [
        threading.Thread(target=run, args=(do_stuff(session),))
        for _ in range(n)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


with ThreadRunner() as runner:
    session = runner.enter_context(factory=aiohttp.ClientSession)
    coroutine = session.get('https://death.andgravity.com/')
    with runner.wrap_context(coroutine) as response:
        lines = [line for line in runner.wrap_iter(response.content)]
    print('got', len(lines), 'lines')
