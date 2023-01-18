import sys
import time
import asyncio
import itertools
import collections.abc


def map_unordered(func, iterable, limit):
    aws = map(func, iterable)
    return limit_concurrency(aws, limit)


async def limit_concurrency(aws, limit):
    aws = iter(aws)
    queue = asyncio.Queue()
    ndone = 0

    async def worker():
        nonlocal ndone

        while True:
            try:
                aw = next(aws)
            except StopIteration:
                ndone += 1
                break

            await queue.put(await aw)

    worker_tasks = [asyncio.create_task(worker()) for _ in range(limit)]

    while ndone < limit or not queue.empty():
        yield await queue.get()


async def sleep(i):
    1 / i
    await asyncio.sleep(i)
    return i


async def async_main(args, limit):
    start = time.monotonic()
    async for result in map_unordered(sleep, args, limit):
        print(f"{(time.monotonic() - start):.1f}: {result}")
    print(f"{(time.monotonic() - start):.1f}: done")


def on_iter_end(it, callback):
    for x in it:
        yield x
    callback()


def main():
    limit = int(sys.argv[1])
    args = [float(n) for n in sys.argv[2:]]
    timeout = sum(args) + 0.1
    args = on_iter_end(args, lambda: print("iter end"))
    asyncio.run(asyncio.wait_for(async_main(args, limit), timeout))


if __name__ == '__main__':
    main()
