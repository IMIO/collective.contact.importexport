# -*- coding: utf-8 -*-

from future.builtins import zip
from collective.contact.core.behaviors import validate_email
from collective.contact.importexport import e_logger
from zope.i18n import translate

import datetime
import os
import phonenumbers
import pycountry
import re
import unicodedata


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


def alphanum(value):
    # filter with str.isalnum or unicode.isalnum
    return filter(type(value).isalnum, value)


def valid_zip(item, zipkey, countrykey):
    """ Check and return valid format zip """
    zipc = digit(item[zipkey])
    if item[zipkey] != zipc:
        input_error(item, u"zip code col '{}' contains non digit chars, value '{}'".format(zipkey, item[zipkey]))
    if zipc and len(zipc) != 4 and not item[countrykey]:
        input_error(item, u"zip code col '{}' length not 4, value '{}' => kept '' value".format(zipkey, item[zipkey]))
        return u''
    return zipc


def valid_phone(item, phonekey, countrykey, default_country, language='en'):
    """ Check and return valid phone """
    phone = digit(item[phonekey])
    if not phone:
        return phone
    countries = [default_country]
    # get country in lower cas without accent
    country = unicodedata.normalize('NFD', item[countrykey].lower()).encode('ascii', 'ignore')
    if country:
        # get english country translation
        tr_ctry = translate(country, domain="to_pycountry_lower", target_language=language, default=u'')
        if tr_ctry == u'':
            input_error(item, u"country col '{}' with value '{}' changed in '{}' cannot be translated, kept '' value "
                              u"for phone number col {}".format(countrykey, item[countrykey], country, phonekey))
            return u''
        # get alpha2 country
        entry = pycountry.countries.get(name=tr_ctry)
        if entry is None:
            input_error(item, u"country col '{}' with value '{}' changed in '{}' cannot be found, kept '' value "
                              u"for phone number col {}".format(countrykey, item[countrykey], tr_ctry, phonekey))
            return u''
        countries.insert(0, entry.alpha_2)

    for ctry in countries:
        try:
            number = phonenumbers.parse(phone, ctry)
            break
        except phonenumbers.NumberParseException:
            pass
    else:
        input_error(item, u"phone number col '{}' with value '{}' cannot be parsed => kept '' value".format(phonekey,
                                                                                                            phone))
        return u''

    if not phonenumbers.is_valid_number(number):
        input_error(item, u"phone number col '{}' with value '{}' is invalid '{}' => kept '' value".format(phonekey,
                          phone, number))
        return u''
    return phone
    # can be done : verify if number region == country
    # from phonenumbers.phonenumberutil import country_code_for_region


def valid_email(item, emailkey):
    """ Check and return valid email """
    if not item[emailkey]:
        return u''
    try:
        validate_email(item[emailkey])
    except:
        input_error(item, u"email col '{}' with invalid value '{}' => kept '' value".format(emailkey, item[emailkey]))
        return u''
    return item[emailkey]


def valid_value_in_list(item, val, lst):
    if val not in lst:
        input_error(item, "value '%s' not in valid values '%s'" % (val, lst))
        return u''
    return val


def valid_date(item, val, fmt='%Y/%m/%d', can_be_empty=True):
    if not val and can_be_empty:
        return None
    try:
        dtm = datetime.datetime.strptime(val, fmt)
        dt = dtm.date()
    except Exception, ex:
        input_error(item, u"not a valid date '%s': %s" % (val, ex))
        return None
    return dt


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


def by3wise(iterable):
    """ Returns tuples of 3 elements: s -> (s0, s1, s3), (s4, s5, s6) ... """
    a = iter(iterable)
    return zip(a, a, a)


def relative_path(portal, fullpath):
    """ return relative path """
    portal_path = '/'.join(portal.getPhysicalPath())
    return fullpath[len(portal_path) + 1:]
