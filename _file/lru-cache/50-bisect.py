import bisect
import operator
import time
import math
from collections import OrderedDict
from typing import NamedTuple


class Cache:

    def __init__(self, maxsize, time=time.monotonic):
        self.maxsize = maxsize
        self.time = time

        self.cache = {}
        self.expires_buckets = {}
        self.expires_order = PriorityQueue()
        self.priority_buckets = {}
        self.priority_order = PriorityQueue()

    def get(self, key):
        item = self.cache.get(key)
        if not item:
            return None

        if self.time() >= item.expires:
            return None

        self.priority_buckets[item.priority].move_to_end(key)
        return item.value

    def set(self, key, value, *, maxage=10, priority=0):
        now = self.time()

        if key in self.cache:
            self.delete(key)
        elif len(self.cache) >= self.maxsize:
            self.evict(now)

        expires = log_bucket(now, maxage, shift=7)
        priority = log_bucket(0, priority+1, shift=7)
        item = Item(key, value, expires, priority)

        self.cache[key] = item

        expires_bucket = self.expires_buckets.get(expires)
        if not expires_bucket:
            expires_bucket = self.expires_buckets[expires] = set()
            self.expires_order.push(expires)
        expires_bucket.add(key)

        priority_bucket = self.priority_buckets.get(priority)
        if not priority_bucket:
            priority_bucket = self.priority_buckets[priority] = OrderedDict()
            self.priority_order.push(priority)
        priority_bucket[key] = None

    def evict(self, now):
        if not self.cache:
            return

        initial_size = len(self.cache)

        while self.cache:
            expires = self.expires_order.peek()
            if expires > now:
                break
            expires_bucket = self.expires_buckets[expires]
            for key in list(self.expires_buckets[expires]):
                self.delete(key)

        if len(self.cache) == initial_size:
            priority = self.priority_order.peek()
            priority_bucket = self.priority_buckets.get(priority)
            key = next(iter(priority_bucket))
            self.delete(key)

    def delete(self, key):
        *_, expires, priority = self.cache.pop(key)

        expires_bucket = self.expires_buckets[expires]
        expires_bucket.remove(key)
        if not expires_bucket:
            del self.expires_buckets[expires]
            self.expires_order.remove(expires)

        priority_bucket = self.priority_buckets[priority]
        del priority_bucket[key]
        if not priority_bucket:
            del self.priority_buckets[priority]
            self.priority_order.remove(priority)


class Item(NamedTuple):
    key: object
    value: object
    expires: int
    priority: int


class PriorityQueue:

    def __init__(self):
        self.data = []

    def push(self, item):
        bisect.insort(self.data, item, key=operator.neg)

    def peek(self):
        return self.data[-1]

    def pop(self):
        return self.data.pop()

    def remove(self, item):
        if item == self.peek():
            self.pop()
            return
        i = bisect.bisect_left(self.data, -item, key=operator.neg)
        if i != len(self.data) and self.data[i] == item:
            del self.data[i]
            return
        raise ValueError

    def __bool__(self):
        return bool(self.data)


def log_bucket(now, maxage, shift=0):
    next_power = 2 ** max(0, math.ceil(math.log2(maxage) - shift))
    expires = now + maxage
    bucket = math.ceil(expires / next_power) * next_power
    return bucket


import random
import functools

def error(now, maxage, *args):
    bucket = log_bucket(now, maxage, *args)
    return (bucket - now) / maxage - 1

def max_error(now, n, *args):
    return max(error(now, i, *args) for i in range(1, n+1))

def max_error_random(n, *args):
    max_now = int(time.time())
    max_maxage = 3600 * 24 * 31
    rand = functools.partial(random.randint, 1)
    return max(
        error(rand(max_now), rand(max_maxage), *args)
        for _ in range(n)
    )

def max_buckets(seconds, *args):
    now = time.time()
    buckets = {log_bucket(now, i, *args) for i in range(1, seconds)}
    return len(buckets)


import pytest


class FakeTime:
    def __init__(self, now=0):
        self.now = now
    def __call__(self):
        return self.now


def test_basic():
    cache = Cache(2, FakeTime())

    assert cache.get('a') == None

    cache.set('a', 'A')
    assert cache.get('a') == 'A'

    cache.set('b', 'B')
    assert cache.get('a') == 'A'
    assert cache.get('b') == 'B'

    cache.set('c', 'C')
    assert cache.get('a') == None
    assert cache.get('b') == 'B'
    assert cache.get('c') == 'C'


def test_expires():
    cache = Cache(2, FakeTime())

    cache.set('a', 'A', maxage=10)
    cache.set('b', 'B', maxage=20)
    assert cache.get('a') == 'A'
    assert cache.get('b') == 'B'

    cache.time.now = 15
    assert cache.get('a') == None
    assert cache.get('b') == 'B'

    cache.set('c', 'C')
    assert cache.get('a') == None
    assert cache.get('b') == 'B'
    assert cache.get('c') == 'C'


def test_update_expires():
    cache = Cache(2, FakeTime())

    cache.set('a', 'A', maxage=10)
    cache.set('b', 'B', maxage=10)

    cache.time.now = 5
    cache.set('a', 'X', maxage=4)
    cache.set('b', 'Y', maxage=6)
    assert cache.get('a') == 'X'
    assert cache.get('b') == 'Y'

    cache.time.now = 10
    assert cache.get('a') == None
    assert cache.get('b') == 'Y'


def test_priorities():
    cache = Cache(2, FakeTime())

    cache.set('a', 'A', priority=1)
    cache.set('b', 'B', priority=0)
    assert cache.get('a') == 'A'
    assert cache.get('b') == 'B'

    cache.set('c', 'C')
    assert cache.get('a') == 'A'
    assert cache.get('b') == None
    assert cache.get('c') == 'C'


def test_update_priorities():
    cache = Cache(2, FakeTime())

    cache.set('a', 'A', priority=1)
    cache.set('b', 'B', priority=0)
    cache.set('b', 'Y', priority=2)

    cache.set('c', 'C')
    assert cache.get('a') == None
    assert cache.get('b') == 'Y'
    assert cache.get('c') == 'C'


def test_lru():
    cache = Cache(2, FakeTime())

    cache.set('a', 'A')
    cache.set('b', 'B')
    cache.get('a') == 'A'

    cache.set('c', 'C')

    assert cache.get('a') == 'A'
    assert cache.get('b') == None
    assert cache.get('c') == 'C'


def test_priority_queue():
    pq = PriorityQueue()
    pq.push(1)
    pq.push(3)
    pq.push(2)

    assert pq
    assert pq.peek() == 1
    assert pq.pop() == 1
    assert pq.peek() == 2

    assert pq.remove(3) is None

    assert pq
    assert pq.peek() == 2
    with pytest.raises(ValueError):
        pq.remove(3)

    assert pq.pop() == 2

    assert not pq
    with pytest.raises(IndexError):
        pq.peek()
    with pytest.raises(IndexError):
        pq.pop()
