# -*- coding: utf-8 -*-
from collective.contact.core.behaviors import InvalidEmailAddress
from future.builtins import zip
from collective.contact.core.behaviors import validate_email
from collective.contact.importexport import e_logger
from collective.contact.importexport.config import ANNOTATION_KEY
from collective.contact.importexport.config import ZIP_DIGIT
from collective.contact.importexport.config import ZIP_PATTERN
from imio.helpers.emailer import add_attachment
from imio.helpers.emailer import create_html_email
from imio.helpers.emailer import send_email
from plone import api
from zope.annotation.interfaces import IAnnotations
from zope.i18n import translate

import datetime
import os
import phonenumbers
import pycountry
import re
import unicodedata


def shortcut(val):
    shortcuts = {u'organization': u'O', u'person': u'P', u'held_position': u'HP', 'new': u'N', 'update': u'U',
                 'delete': u'D'}
    if val in shortcuts:
        return shortcuts[val]
    return val


def log_error(item, msg, level='error'):
    getattr(e_logger, level)(u'{}: {}, ln {:d}, {}'.format(item['_set'], shortcut(item['_type']), item['_ln'], msg))
    item['_error'] = True


def digit(phone):
    # filter with str.isdigit or unicode.isdigit
    return filter(type(phone).isdigit, phone)


def alphanum(value):
    # filter with str.isalnum or unicode.isalnum
    return filter(type(value).isalnum, value)


def get_country_code(item, countrykey, default_country, languages=(u'en', )):
    """ Get country code """
    # get country in lower case without accent
    country = unicodedata.normalize('NFD', item[countrykey].lower()).encode('ascii', 'ignore')
    if not country:
        return None
    # get english country translation
    for language in languages:
        tr_ctry = translate(country, domain="to_pycountry_lower", target_language=language, default=u'')
        if tr_ctry != u'':
            break
    else:
        log_error(item, u"country col '{}' with value '{}' changed in '{}' cannot be translated: "
                        u"complete po file if necessary ?".format(countrykey, item[countrykey], country))
        return u''
    # get alpha2 country
    entry = pycountry.countries.get(name=tr_ctry)
    if entry is None:
        log_error(item, u"country col '{}' with value '{}' translated in '{}' cannot be found".format(
            countrykey, item[countrykey], tr_ctry))
        return u''
    return entry.alpha_2


def valid_zip(item, zipkey, countrycode):
    """ Check and return valid format zip """
    zipc = item[zipkey]
    if not zipc:
        return zipc
    if countrycode is None:
        countrycode = u'BE'
    if countrycode in ZIP_DIGIT:
        zipc = digit(item[zipkey])
        # if item[zipkey] != zipc:
        #     log_error(item, u"zip code col '{}' for country '{}' contains non digit chars, orig value '{}' => "
        #                     u"'{}'".format(zipkey, countrycode, item[zipkey], zipc))
    if countrycode in ZIP_PATTERN:
        match = ZIP_PATTERN[countrycode].match(zipc)
        if match is None:
            log_error(item, u"zip code col '{}' for country '{}' with value '{}' doesn't match pattern '{}', "
                            u"kept '{}'".format(zipkey, countrycode, item[zipkey],
                                                ZIP_PATTERN[countrycode].pattern, zipc))
    else:
        log_error(item, u"can't check zip code col '{}' for country '{}' with value '{}', kept '{}'".format(
                          zipkey, countrycode, item[zipkey], zipc))
    return zipc


def valid_phone(item, phonekey, countrycode, default_country):
    """ Check and return valid phone """
    phone = digit(item[phonekey])
    if not phone:
        return phone
    if countrycode == u'':  # problem converting non empty country
        log_error(item, u"can't check phone col '{}' with value '{}', kept ''".format(
                          phonekey, item[phonekey]))
        return u''
    countries = [default_country]
    if countrycode and countrycode != default_country:
        countries.insert(0, countrycode)

    for ctry in countries:
        try:
            number = phonenumbers.parse(phone, ctry)
            break
        except phonenumbers.NumberParseException:
            pass
    else:
        log_error(item, u"phone number col '{}' with value '{}' cannot be parsed => kept '' value".format(phonekey,
                                                                                                          phone))
        return u''

    if not phonenumbers.is_valid_number(number):
        log_error(item, u"phone number col '{}' with value '{}' is invalid '{}' => kept '' value".format(
                          phonekey, phone, number))
        return u''
    return phone
    # can be done : verify if number region == country
    # from phonenumbers.phonenumberutil import country_code_for_region


def valid_email(item, emailkey):
    """ Check and return valid email """
    emailv = item[emailkey].strip(',; ')
    if not emailv:
        return u''
    emailv = unicodedata.normalize('NFD', emailv.lower()).encode('ascii', 'ignore')
    try:
        validate_email(emailv)
    except InvalidEmailAddress:
        log_error(item, u"email col '{}' with orig value '{}' changed in '{}' => kept '' value".format(emailkey,
                  item[emailkey], emailv))
        return u''
    return emailv.lower()


def valid_value_in_list(item, val, lst):
    if val not in lst:
        log_error(item, "value '%s' not in valid values '%s'" % (val, lst))
        return u''
    return val


def send_report(portal, lines):
    """Send email if required."""
    emails = api.portal.get_registry_record('collective.contact.importexport.interfaces.IPipelineConfiguration.emails')
    if not emails:
        return
    msg = create_html_email(u'\n'.join([u'<p>{}</p>'.format(line) for line in lines]))
    annot = IAnnotations(portal).get(ANNOTATION_KEY)
    for filename in ('ie_input_errors.log', 'ie_shortlog.log'):
        path = os.path.join(annot['wp'], filename)
        add_attachment(msg, filename, filepath=path)
    mfrom = portal.getProperty('email_from_address')
    ret, error = send_email(msg, u'Contact import report', mfrom, emails)
    if not ret:
        with open(os.path.join(annot['wp'], 'ie_input_errors.log'), 'a') as f:
            f.write('Your email has not been sent: {}'.format(error))
