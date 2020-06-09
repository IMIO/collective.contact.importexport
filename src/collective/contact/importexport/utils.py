# -*- coding: utf-8 -*-

from builtins import zip  # from future package
from collective.contact.core.behaviors import validateEmail
from collective.contact.importexport import e_logger

import os
import phonenumbers
import re


def input_error(item, msg):
    e_logger.error(u'{}: ln {:d}, {}'.format(item['_type'], item['_ln'], msg))


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
        else:
            path = os.getenv('PWD')
    if subpath:
        path = os.path.join(path, subpath)
    if os.path.exists(path):
        return path
    raise Exception("Path '{}' doesn't exist".format(path))


def to_bool(item, key):
    try:
        return bool(int(item[key] or 0))
    except:
        input_error(item, u"Cannot change '{}' key value '{}' to bool".format(key, item[key]))
    return False


def digit(phone):
    # filter with str.isdigit or unicode.isdigit
    return filter(type(phone).isdigit, phone)


def valid_zip(item, zipkey, countrykey):
    """ Check and return valid format zip """
    zipc = digit(item[zipkey])
    if item[zipkey] != zipc:
        input_error(item, u"zip code col '{}' contains non digit chars, value '{}'".format(zipkey, item[zipkey]))
    if zipc and len(zipc) != 4 and not item[countrykey]:
        input_error(item, u"zip code col '{}' length not 4, value '{}' => kept '' value".format(zipkey, item[zipkey]))
        return u''
    return zipc


def valid_phone(item, phonekey, countrykey):
    """ Check and return valid phone """
    phone = item[phonekey]
    if not phone:
        return phone
    country = item[countrykey].lower()
    countries = {'belgique': 'BE', 'france': 'FR'}
    if not country:
        ctry = 'BE'
    elif country in countries:
        ctry = countries[country]
    else:
        input_error(item, u"country col '{}' with undetected value '{}', kept phone number col {} with value '{}'".format(
                          countrykey, item[countrykey], phonekey, phone))
        return phone
    try:
        number = phonenumbers.parse(phone, ctry)
    except phonenumbers.NumberParseException:
        input_error(item, u"phone number col '{}' with bad value '{}' => kept '' value".format(phonekey, phone))
        return u''
    if not phonenumbers.is_valid_number(number):
        input_error(item, u"phone number col '{}' with invalid value '{}' => kept '' value".format(phonekey, phone))
        return u''
    return phone


def valid_email(item, emailkey):
    """ Check and return valid email """
    if not item[emailkey]:
        return u''
    try:
        validateEmail(item[emailkey])
    except:
        input_error(item, u"email col '{}' with invalid value '{}' => kept '' value".format(emailkey, item[emailkey]))
        return u''
    return item[emailkey]


def correct_path(portal, path):
    """ Check if a path already exists on obj """
    original = path
    i = 1
    while portal.unrestrictedTraverse(path, default=None) is not None:  # path exists
        path = '{}-{:d}'.format(original, i)
        i += 1
    return path


def pairwise(iterable):
    """ s -> (s0, s1), (s2, s3), (s4, s5), ... """
    a = iter(iterable)
    return zip(a, a)


def relative_path(portal, fullpath):
    """ return relative path """
    portal_path = '/'.join(portal.getPhysicalPath())
    return fullpath[len(portal_path) + 1:]
