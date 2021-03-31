import sys
import os

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

def resource_path(relativePath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    basePath = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(basePath, relativePath)
