# coding: utf-8
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
import unittest as _unittest
import gevent
import gevent.event
import traceback

__all__ = ["Scope", "ScopedObject", "AggregateException"]

class ScopedObject(object):
    def __init__(self):
        self._scope = Scope()
        self._scope.__enter__()
    def __enter__(self): 
        return self
    def __exit__(self, exc_type, exc_value, traceback_):
        self._scope.__exit__(exc_type, exc_value, traceback_)
    def close(self):
        self.__exit__(None,None,None)
    @property
    def closed(self):
        return self._scope.closed
    

class Scope(object):
    def __init__(self, on_exit=None):
        self._exit_handlers = list(reversed(on_exit or []))
        self._is_closing = False
        self.closed = gevent.event.Event()
        
    def on_exit(self, *args):
        self._exit_handlers.extend(reversed(args))
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback_):
        if self._is_closing: return
        self._is_closing = True
        exceptions = []
        for exit_handler in reversed(self._exit_handlers):
            try:
                exit_handler()
            except Exception as e: #Catching all exceptions by intent. They are taken care of in the AggregateExceptions . | pylint: disable=W0703
                exceptions.append((e,traceback.format_exc()))
        self.closed.set()
        if exceptions:
            raise AggregateException(exceptions)
                

class AggregateException(Exception):
    def __init__(self, exceptions):
        message = self.create_message(exceptions)
        Exception.__init__(self, message)
        self.exceptions = exceptions
        
    @classmethod
    def create_message(cls, exceptions):
        n=len(exceptions)
        res = "Aggregate exception with {} inner exceptions\n".format(n)
        i = 1
        for (e,exc) in exceptions:
            res = ("{res}===Start inner exception {i} of {n}===\n"
                   "{exc}===End inner exception {i} of {n}===\n"
                   .format(res=res,i=i,n=n,exc=exc))
            i = i+1
        return res


class Test_Scope(_unittest.TestCase):
    def test_simple(self):
        inserted = "delayed"
        with Scope() as s:
            l=[]
            s.on_exit(lambda: l.append(inserted))
            self.assertSequenceEqual(l, [], "Nothing should be added yet")
        self.assertSequenceEqual(l, [inserted], "Now \"{}\" should be added".format(inserted))

    def test_reversed_order_of_execution(self):
        with Scope() as s:
            l=[]
            m=[]
            s.on_exit(lambda: l.append("Anything"))
            s.on_exit(lambda: m.append(len(l)))
        self.assertSequenceEqual(m, [0], "The second lambda should be run first")

    def test_original_order_of_execution_in_same_call(self):
        with Scope() as s:
            l=[]
            m=[]
            s.on_exit(lambda: m.append(len(l)), lambda: l.append("Anything"))
        self.assertSequenceEqual(m, [0], "The first lambda should be run first")
        
    def test_constructor(self):
        l=[]
        m=[]
        with Scope(on_exit=[lambda: m.append(len(l)), lambda: l.append("Anything")]):
            self.assertSequenceEqual(l, [], "Nothing should be added yet")
        self.assertSequenceEqual(m, [0], "The first lambda should be run first")

    def test_constructor_and_extra_on_exit(self):
        l=[]
        m=[]
        with Scope(on_exit=[lambda: l.append("Anything")]) as s:
            s.on_exit(lambda: m.append(len(l)))
            self.assertSequenceEqual(l, [], "Nothing should be added yet")
        self.assertSequenceEqual(m, [0], "The first lambda should be run first")
        
    def test_exception(self):
        l=[]
        try:
            with Scope(on_exit=[lambda: l.append("Anything")]):
                raise Exception
        except:
            pass
        self.assertEqual(len(l), 1, "The on_exit lambda should have been run, even in case of an exception")
        
    def test_exception_in_handler(self):
        didThrow = False
        def f1(): 
            raise Exception("1")
        def f2(): 
            raise Exception("2")
        def f():
            with Scope() as s:
                s.on_exit(f2)
                s.on_exit(f1)
                pass
        try:
            f()
        except AggregateException as e:
            traceback.print_exc()
            self.assertEqual(len(e.exceptions), 2)
            for i in range(2):
                self.assertEqual(e.exceptions[i][0].message, str(i+1))
            didThrow = True
        self.assert_(didThrow)
            
                
if __name__ == '__main__':
    _unittest.main()
