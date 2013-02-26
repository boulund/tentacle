#import as local alias to facilitate from utils import * without getting them
import unittest as _unittest
import Queue as _Queue

__all__ = ["dequeueingIteration"]

def dequeueingIteration(q):
    try:
        while True:
            yield q.get_nowait()
    except _Queue.Empty:
        pass

class _Test_dequeueingIteration(_unittest.TestCase):
    def _doTest(self, l):
        q = _Queue.Queue()
        for i in l:
            q.put(i)
        copy = list(dequeueingIteration(q))
        self.assertSequenceEqual(copy, l)
    
    def test_no_data(self):
        self._doTest([])

    def test_one_data(self):
        self._doTest([1])

    def test_some_data(self):
        self._doTest([1,2,3])

if __name__ == '__main__':
    _unittest.main()