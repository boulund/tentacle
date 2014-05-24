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
import os

__all__ = list()

__all__.append("fmt")
def fmt(in_str):
    in_str.format(**globals())


__all__.append("printer")
def printer(msg):
    def p():
        print msg
    return p


__all__.append("ExecutableNotFound")
__all__.append("resolve_executable")
class ExecutableNotFound(Exception): pass
def resolve_executable(program, fallback=None):
    #inspired by http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
    import platform
    
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    
    dirs = [s.strip('"') for s in os.environ["PATH"].split(os.pathsep)]
    current_file_dir = os.path.dirname(os.path.realpath(__file__)) 
    valids = filter(is_exe,[os.path.join(path, program) for path in dirs])
    if valids:
        return valids[0]
    if fallback:
        return fallback
    raise ExecutableNotFound("Could not find \"{}\" among \"{}\".".format(program, ":".join(dirs)))


__all__.append("assert_file_exists")
class FileNotFound(Exception): pass
def assert_file_exists(fileDesc, fileName):
    if not os.path.isfile(fileName):
        print "ERROR: " + fileDesc.capitalize() + " file not supplied correctly ("+ fileName +")."
        raise FileNotFound(fileName)


#def call(o, arguments):
#    o.__call__(*arguments.get('args',list()), **arguments.get('kwargs',dict()))
