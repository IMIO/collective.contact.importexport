from collective.contact.core.behaviors import InvalidEmailAddress
from collective.contact.core.behaviors import validate_email
from collective.contact.importexport import e_logger
from collective.contact.importexport import T_S
from collective.contact.importexport.config import ANNOTATION_KEY
from collective.contact.importexport.config import ZIP_DIGIT
from collective.contact.importexport.config import ZIP_PATTERN
from imio.helpers.emailer import add_attachment
from imio.helpers.emailer import create_html_email
from imio.helpers.emailer import send_email
from imio.helpers.transmogrifier import key_val as shortcut
from plone import api
from zope.annotation.interfaces import IAnnotations
from zope.i18n import translate

import os
import phonenumbers
import pycountry
import unicodedata


def log_error(item, msg, level="error"):
    getattr(e_logger, level)("{}: {}, ln {:d}, {}".format(item["_set"], shortcut(item["_type"], T_S), item["_ln"], msg))
    item["_error"] = True


def digit(phone):
    # filter with str.isdigit or unicode.isdigit
    return "".join(filter(str.isdigit, phone))


def alphanum(value):
    # filter with str.isalnum or unicode.isalnum
    return "".join(filter(str.isalnum, value))


def get_country_code(item, countrykey, default_country, languages=("en",)):
    """Get country code"""
    # get country in lower case without accent
    country = unicodedata.normalize("NFD", item[countrykey].lower()).encode("ascii", "ignore").decode()
    if not country:
        return None
    # get english country translation
    for language in languages:
        tr_ctry = translate(country, domain="to_pycountry_lower", target_language=language, default="")
        if tr_ctry != "":
            break
    else:
        log_error(
            item,
            "country col '{}' with value '{}' changed in '{}' cannot be translated: "
            "complete po file if necessary ?".format(countrykey, item[countrykey], country),
        )
        return ""
    # get alpha2 country
    entry = pycountry.countries.get(name=tr_ctry)
    if entry is None:
        log_error(
            item,
            "country col '{}' with value '{}' translated in '{}' cannot be found".format(
                countrykey, item[countrykey], tr_ctry
            ),
        )
        return ""
    return entry.alpha_2


def valid_zip(item, zipkey, countrycode):
    """Check and return valid format zip"""
    zipc = item[zipkey]
    if not zipc:
        return zipc
    if countrycode is None:
        countrycode = "BE"
    if countrycode in ZIP_DIGIT:
        zipc = digit(item[zipkey])
        # if item[zipkey] != zipc:
        #     log_error(item, u"zip code col '{}' for country '{}' contains non digit chars, orig value '{}' => "
        #                     u"'{}'".format(zipkey, countrycode, item[zipkey], zipc))
    if countrycode in ZIP_PATTERN:
        match = ZIP_PATTERN[countrycode].match(zipc)
        if match is None:
            log_error(
                item,
                "zip code col '{}' for country '{}' with value '{}' doesn't match pattern '{}', "
                "kept '{}'".format(zipkey, countrycode, item[zipkey], ZIP_PATTERN[countrycode].pattern, zipc),
            )
    else:
        log_error(
            item,
            "can't check zip code col '{}' for country '{}' with value '{}', kept '{}'".format(
                zipkey, countrycode, item[zipkey], zipc
            ),
        )
    return zipc


def valid_phone(item, phonekey, countrycode, default_country):
    """Check and return valid phone"""
    phone = digit(item[phonekey])
    if not phone:
        return phone
    if countrycode == "":  # problem converting non empty country
        log_error(item, "can't check phone col '{}' with value '{}', kept ''".format(phonekey, item[phonekey]))
        return ""
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
        log_error(
            item, "phone number col '{}' with value '{}' cannot be parsed => kept '' value".format(phonekey, phone)
        )
        return ""

    if not phonenumbers.is_valid_number(number):
        log_error(
            item,
            "phone number col '{}' with value '{}' is invalid '{}' => kept '' value".format(phonekey, phone, number),
        )
        return ""
    return phone
    # can be done : verify if number region == country
    # from phonenumbers.phonenumberutil import country_code_for_region


def valid_email(item, emailkey):
    """Check and return valid email"""
    emailv = item[emailkey].strip(",; ")
    if not emailv:
        return ""
    emailv = unicodedata.normalize("NFD", emailv.lower()).encode("ascii", "ignore").decode()
    try:
        validate_email(emailv)
    except InvalidEmailAddress:
        log_error(
            item,
            "email col '{}' with orig value '{}' changed in '{}' => kept '' value".format(
                emailkey, item[emailkey], emailv
            ),
        )
        return ""
    return emailv.lower()


def valid_value_in_list(item, val, lst):
    if val not in lst:
        log_error(item, "value '%s' not in valid values '%s'" % (val, lst))
        return ""
    return val


def send_report(portal, lines):
    """Send email if required."""
    emails = api.portal.get_registry_record("collective.contact.importexport.interfaces.IPipelineConfiguration.emails")
    if not emails:
        return
    msg = create_html_email("\n".join(["<p>{}</p>".format(line) for line in lines]))
    annot = IAnnotations(portal).get(ANNOTATION_KEY)
    for filename in ("ie_input_errors.log", "ie_shortlog.log"):
        path = os.path.join(annot["wp"], filename)
        add_attachment(msg, filename, filepath=path)
    mfrom = api.portal.get_registry_record("plone.email_from_address")
    ret, error = send_email(msg, "Contact import report", mfrom, emails)
    if not ret:
        with open(os.path.join(annot["wp"], "ie_input_errors.log"), "a") as f:
            f.write("Your email has not been sent: {}".format(error))
