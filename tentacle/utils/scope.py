import unittest as _unittest

class Scope(object):
    def __init__(self, on_exit=[]):
        self.exit_handlers = list(reversed(on_exit))
        self.exit_handlers_has_run = False
        
    def on_exit(self, *args):
        self.exit_handlers.extend(reversed(args))
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        #ed = ExceptionDescription(exc_type, exc_value, traceback)
        if self.exit_handlers_has_run:
            return
        for exit_handler in reversed(self.exit_handlers):
            self.exit_handlers_has_run = True
            try:
                exit_handler()
            except:
                print "Exception in exitHandle of Scope. Skipping.\n" + traceback.format_exc()
                
class _Test_Scope(_unittest.TestCase):
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
        
if __name__ == '__main__':
    _unittest.main()