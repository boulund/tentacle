import cPickle
from cStringIO import StringIO

__all__ = ["PickleSerializer"]
class PickleSerializer(object):
    def serialize_to_stream(self, obj, stream):
        cPickle.dump(obj, stream)

    def serialize_to_string(self, obj):
        with StringIO() as f:
            self.serialize_to_stream(obj, f)
            return f.getvalue()
    
    def serialize_to_file(self, obj, obj_file_path):
        with open(obj_file_path, 'w') as f:
            self.serialize_to_stream(obj, f)
    
    def deserialize_from_stream(self, f):
        return cPickle.load(f)
    
    def deserialize_from_string(self, s):
        with StringIO(s) as f:
            return self.deserialize_from_stream(f)
        
    def deserialize_from_file(self, obj_file_path):
        with open(obj_file_path, 'r') as f:
            return self.deserialize_from_stream(f)