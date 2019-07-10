# -*- coding: utf-8 -*-

import os
import re


def get_main_path(path='', subpath=''):
    """
        Return path/subpath if it exists.
        If path is empty, return buildout path.
    """
    if not path:
        # Are we in a classic buildout
        INSTANCE_HOME = os.getenv('INSTANCE_HOME')  # to avoid getting pyflakes error on INSTANCE_HOME
        match = re.match('(.+)/parts/.+', INSTANCE_HOME)
        if match:
            path = match.group(1)
    if subpath:
        path = os.path.join(path, subpath)
    if os.path.exists(path):
        return path
    return None
