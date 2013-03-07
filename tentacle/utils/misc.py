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


__all__.append("resolve_executable")
def resolve_executable(program):
    #inspired by http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
    import platform
    
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    
    dirs = [s.strip('"') for s in os.environ["PATH"].split(os.pathsep)]
    current_file_dir = os.path.dirname(os.path.realpath(__file__)) 
    dirs.append(os.path.join(current_file_dir,"dependencies","bin",platform.system())) #e.g. SOMEDIR/dependencies/bin/Linux
    valids = filter(is_exe,[os.path.join(path, program) for path in dirs])
    if valids:
        return valids[0]
    return None


__all__.append("assert_file_exists")
def assert_file_exists(fileDesc, fileName):
    if not os.path.isfile(fileName):
        print "ERROR: " + fileDesc.capitalize() + " file not supplied correctly ("+ fileName +")."
        exit(1) 


#def call(o, arguments):
#    o.__call__(*arguments.get('args',list()), **arguments.get('kwargs',dict()))