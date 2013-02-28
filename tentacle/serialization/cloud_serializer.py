import cloud.serialization

__all__ = ["CloudSerializer"]
class CloudSerializer(object):
    def serialize_to_string(self, obj):
        return cloud.serialization.serialize(obj,True)
    
    def serialize_to_stream(self, obj, stream):
        s = self.serialize_to_string(obj)
        stream.write(s)

    def serialize_to_file(self, obj, obj_file_path):
        with open(obj_file_path, 'w') as f:
            self.serialize_to_stream(obj, f)
    
    def deserialize_from_string(self, s):
        return cloud.serialization.deserialize(s)
        
    def deserialize_from_stream(self, f):
        s = f.read()
        return self.deserialize_from_string(s)
    
    def deserialize_from_file(self, obj_file_path):
        with open(obj_file_path, 'r') as f:
            return self.deserialize_from_stream(f)

