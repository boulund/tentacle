import unittest as _unittest
import gevent.queue
import random

__all__ = ["IsClosed", "IterableQueue"]

class IsClosed(Exception): pass

class IterableQueue():
    def __init__(self, *args):
        self._inner_queue = gevent.queue.Queue()
        self._is_closed = False
        self.put_many(args)
    def close(self):
        try:
            self._is_closed = True
            self._inner_queue.put(StopIteration)
        except IsClosed: 
            pass
    def put(self, item):
        if self._is_closed:
            raise IsClosed
        self._inner_queue.put(item)
    def put_many(self, items):
        if self._is_closed:
            raise IsClosed
        for item in items:
            self._inner_queue.put(item)
    #iterable and iterator
    def __iter__(self):
        return self
    def next(self):
        result = self._inner_queue.get()
        if result is StopIteration:
            self._inner_queue.put(result) #Keep the StopIteration token in the queue
            raise result
        return result

class Test_IterableQueue(_unittest.TestCase):
    def test_empty(self):
        q = IterableQueue()
        q.close()
        self.assertSequenceEqual([], list(q))
    def test_ordered_put(self):
        l = range(2)
        q = IterableQueue()
        for i in l:
            q.put(i)
        q.close()
        self.assertSequenceEqual(l, list(q))
        self.assertSequenceEqual([], list(q))
    def test_constructor(self):
        l = range(2)
        q = IterableQueue(*l)
        q.close()
        self.assertSequenceEqual(l, list(q))
        self.assertSequenceEqual([], list(q))
    def test_ordered_putMany(self):
        l = range(2)
        q = IterableQueue()
        q.put_many(l)
        q.close()
        self.assertSequenceEqual(l, list(q))
        self.assertSequenceEqual([], list(q))
    def test_concurrent(self):
        l = range(1000)
        q = IterableQueue()
        l2 = []
        write_yield_rate = 0.1
        read_yield_rate = 0.8
        #Each time a reader/writer yields, the control is passed over to the other thread.
        #Setting the reader yield rate lower than the writer yieild rate acts so that the 
        #reader sometimes empties the queue and has to wait
        def write():
            for i in l:
                do_yield=(random.random()<write_yield_rate)
                if do_yield:
                    gevent.sleep(0)
                q.put(i)
            q.close()
        def read():
            for i in q:
                l2.append(i)
                do_yield=(random.random()<read_yield_rate)
                if do_yield:
                    gevent.sleep(0)
        writer = gevent.spawn(write)
        readers = [gevent.spawn(read) for _ in range(10)]
        gevent.joinall(readers + [writer])
        self.assertSequenceEqual(l, l2)
        
    def test_is_closed(self):
        q = IterableQueue()
        q.close()
        self.assertRaises(IsClosed, lambda: q.put_many(1))
        
        
        