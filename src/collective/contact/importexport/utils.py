# -*- coding: utf-8 -*-

import os
import re
import phonenumbers


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
    raise Exception("Path '{}' doesn't exist".format(path))


def is_valid_zip(zipc, country):
    if not zipc:
        return False
    elif zipc and zipc.isdigit and len(zipc) != 4 and not country:
        return False
    else:
        return True


def is_valid_phone(phone, country):
    if not phone:
        return False
    country = country.lower()
    countries = {'belgique': 'BE', 'france': 'FR'}
    if not country:
        ctry = 'BE'
    elif country in countries:
        ctry = countries[country]
    else:
        return False
    try:
        number = phonenumbers.parse(phone, ctry)
    except phonenumbers.NumberParseException:
        return False
    if not phonenumbers.is_valid_number(number):
        return False
    return True
