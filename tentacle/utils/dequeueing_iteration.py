#  Copyright (C) 2014  Fredrik Boulund and Anders Sjögren
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
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
