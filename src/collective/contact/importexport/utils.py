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
    raise Exception("Path '{}' doesn't exist".format(path))


def digit(phone):
    # filter with str.isdigit or unicode.isdigit
    return filter(type(phone).isdigit, phone)

def is_zip(zipc, line, typ, country):
    ozipc = zipc
    zipc = digit(zipc)
    if ozipc != zipc:
        out.append("!! %s: line %d, zip code contains non digit chars: %s" % (typ, line, zipc))
    if zipc and len(zipc) != 4 and not country:
        out.append("!! %s: line %d, zip code length not 4: %s" % (typ, line, zipc))
    if zipc in ['0']:
        return ''
    return zipc

def check_phone(phone, line, typ, country):
    if not phone:
        return phone
    country = country.lower()
    countries = {'belgique': 'BE', 'france': 'FR'}
    if not country:
        ctry = 'BE'
    elif country in countries:
        ctry = countries[country]
    else:
        out.append("!! %s: line %d, country not detected '%s', phone number: '%s'" % (typ, line, country, phone))
        return phone
    try:
        number = phonenumbers.parse(phone, ctry)
    except phonenumbers.NumberParseException:
        out.append("!! %s: line %d, bad phone number: %s" % (typ, line, phone))
        return ''
    if not phonenumbers.is_valid_number(number):
        out.append("!! %s: line %d, invalid phone number: %s" % (typ, line, phone))
        return ''
    return phone
