import sys, os

# def we_are_frozen():
#     # All of the modules are built-in to the interpreter, e.g., by py2exe
#     return hasattr(sys, "frozen")
# 
# def module_path():
#     encoding = sys.getfilesystemencoding()
#     if we_are_frozen():
#         return os.path.dirname(unicode(sys.executable, encoding))
#     return os.path.dirname(unicode(__file__, encoding))

def module_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))