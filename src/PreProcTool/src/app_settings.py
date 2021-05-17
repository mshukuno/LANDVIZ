import logging.config
import os
import sys
import yaml


def module_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(relativePath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    basePath = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(basePath, relativePath)


def get_app_path():
    """
    Get application path.
    @return str app_path: The PreProcTool application directory
    """
    app_path = module_path()
    return app_path


def get_app_file():
    """
    Get currently running Python file name.
    @return str app_file:
    """
    app_file = os.path.split(os.path.normpath(os.path.realpath(__file__)))[1]
    return app_file


def set_env_proj_lib():
    """
    Set PROJ_LIB environment path.
    Case 1: Run executable -> Set env by runtime hook
    Case 2: Run main.py
    @raise KeyError
    """
    try:
        if os.environ['PROJ_LIB']:
            pass

    except KeyError:
        os.environ['PROJ_LIB'] = os.path.join(os.path.dirname(sys.argv[0]), 'proj')


def setup_logger(log_file_name):
    """
    Set logging system for LANDIVIZ PreProcTool.
    @param str log_file_name: Log file name
    """
    app_path = module_path()
    logs_dir = os.path.join(app_path, 'logs')
    logging_yaml = os.path.join(app_path, 'config', 'logging.yaml')
    logs_file = os.path.join(logs_dir, log_file_name)

    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    with open(logging_yaml, 'r') as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)
    config['handlers']['file_handler']['filename'] = logs_file
    logging.config.dictConfig(config)
    # logging.config.dictConfig({'version': 1, 'disable_existing_loggers': False})


def error_log(logger, err):
    """
    Set error log format and write to a log file.
    @param logger logger: Logger object
    @param Exception err: Exception object
    """
    trace = []
    tb = err.__traceback__
    while tb is not None:
        path = os.path.normpath(tb.tb_frame.f_code.co_filename)
        path_last_two_level = '/'.join(path.split(os.sep)[-2:])
        trace.append({
            "filename": path_last_two_level,
            "name": tb.tb_frame.f_code.co_name,
            "line": tb.tb_lineno
        })
        tb = tb.tb_next
    last_trace = trace[-1]
    msg = f'{type(err).__name__}\t{last_trace["filename"]}:{last_trace["line"]}\n\t{str(err)}'
    logger.error(msg)


