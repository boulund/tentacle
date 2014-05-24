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
