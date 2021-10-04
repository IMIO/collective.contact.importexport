# -*- coding: utf-8 -*-

import re

ANNOTATION_KEY = 'collective.contact.importexport'

ZIP_DIGIT = [u'AT', u'AU', u'BE', u'BG', u'CH', u'CN', u'CY', u'DE', u'DK', u'DZ', u'EE', u'ES', u'FI', u'FR',
             u'GF', u'HR', u'HU', u'ID', u'IL', u'IN', u'IS', u'IT', u'JO', u'KE', u'KR', u'KW', u'KZ', u'LK',
             u'LU', u'LV', u'LT', u'MC', u'MD', u'MG', u'MU', u'MX', u'MY', u'MZ', u'NC', u'NO', u'NZ', u'PH',
             u'RE', u'RO', u'RS', u'RU', u'SG', u'SI', u'SN', u'TH', u'TN', u'TR', u'US', u'UY', u'VN', u'ZA']
# Based on https://en.wikipedia.org/wiki/List_of_postal_codes
ZIP_PATTERN = {
    u'AD': re.compile(r'(AD)?\d{3}$'),  # 3 digits
    u'AE': re.compile(r'.+$'),  # no standard
    u'AR': re.compile(r'(\d{4}|\w\d{4}|\w\d{4}\w{3})$'),  # 4 digits or ...
    u'AT': re.compile(r'\d{4}$'),  # 4 digits
    u'AU': re.compile(r'\d{4}$'),  # 4 digits
    u'BE': re.compile(r'\d{4}$'),  # 4 digits
    u'BF': re.compile(r'.+$'),  # no standard
    u'BG': re.compile(r'\d{4}$'),  # 4 digits
    u'BM': re.compile(r'.+$'),  # no standard
    u'BR': re.compile(r'\d{5}( |-)\d{3}$'),  # 5 dig - 3 dig
    u'BW': re.compile(r'.+$'),  # no standard
    u'CA': re.compile(r'\w{3} *\w{3}$'),  # 3 chars 3 chars
    u'CD': re.compile(r'.+$'),  # no standard
    u'CG': re.compile(r'.+$'),  # no standard
    u'CH': re.compile(r'\d{4}$'),  # 4 digits
    u'CN': re.compile(r'\d{6}$'),  # 6 digits
    u'CY': re.compile(r'\d{4}$'),  # 4 digits
    u'CZ': re.compile(r'\d{3} *\d{2}$'),  # 3 dig 2 dig
    u'DE': re.compile(r'\d{5}$'),  # 5 digits
    u'DK': re.compile(r'\d{4}$'),  # 4 digits
    u'DZ': re.compile(r'\d{5}$'),  # 5 digits
    u'EE': re.compile(r'\d{5}$'),  # 5 digits
    u'ES': re.compile(r'\d{5}$'),  # 5 digits
    u'FI': re.compile(r'\d{5}$'),  # 5 digits
    u'FR': re.compile(r'\d{5}$'),  # 5 digits
    u'GB': re.compile(r'.+$'),  # to funny
    u'GF': re.compile(r'\d{5}$'),  # 5 digits
    u'GG': re.compile(r'.+$'),  # to funny
    u'GI': re.compile(r'.+$'),  # to funny
    u'GR': re.compile(r'\d{3} *\d{2}$'),  # 3 dig 2 dig
    u'HK': re.compile(r'.+$'),  # no standard
    u'HR': re.compile(r'\d{5}$'),  # 5 digits
    u'HU': re.compile(r'\d{4}$'),  # 4 digits
    u'ID': re.compile(r'\d{5}$'),  # 5 digits
    u'IE': re.compile(r'.+$'),  # to funny
    u'IL': re.compile(r'\d{5}(\d{2})$'),  # 5 or 7 digits
    u'IN': re.compile(r'\d{6}$'),  # 6 digits
    u'IS': re.compile(r'\d{3}$'),  # 3 digits
    u'IT': re.compile(r'\d{5}$'),  # 5 digits
    u'JO': re.compile(r'\d{5}$'),  # 5 digits
    u'JP': re.compile(r'\d{3}( *|-)\d{4}$'),  # 3 dig - 4 dig
    u'KE': re.compile(r'\d{5}$'),  # 5 digits
    u'KW': re.compile(r'\d{5}$'),  # 5 digits
    u'KR': re.compile(r'\d{5}$'),  # 5 digits
    u'KZ': re.compile(r'\d{6}$'),  # 6 digits
    u'LB': re.compile(r'(\d{5}|\d{4} *\d{4})$'),  # 5 dig or 4 4
    u'LK': re.compile(r'\d{5}$'),  # 5 digits
    u'LU': re.compile(r'\d{4}$'),  # 4 digits
    u'LV': re.compile(r'\d{4}$'),  # 4 digits
    u'LT': re.compile(r'\d{5}$'),  # 5 digits
    u'MA': re.compile(r'\d{2} *\d{3}$'),  # 5 digits with spaces
    u'MC': re.compile(r'980\d{2}$'),  # 5 digits
    u'MD': re.compile(r'\d{4}$'),  # 4 digits
    u'MG': re.compile(r'\d{3}$'),  # 3 digits
    u'MU': re.compile(r'\d{5}$'),  # 5 digits
    u'MX': re.compile(r'\d{5}$'),  # 5 digits
    u'MY': re.compile(r'\d{5}$'),  # 5 digits
    u'MZ': re.compile(r'\d{4}$'),  # 4 digits
    u'MT': re.compile(r'\w{3} *\d{4}$'),  # 3 chars 4 digits
    u'NC': re.compile(r'988\d{2}$'),  # 5 digits
    u'NL': re.compile(r'\d{4}( *\w{2})?$'),  # 4 digits 2 letters?
    u'NO': re.compile(r'\d{4}$'),  # 4 digits
    u'NZ': re.compile(r'\d{4}$'),  # 4 digits
    u'PH': re.compile(r'\d{3,4}$'),  # 3 or 4 digits
    u'PL': re.compile(r'\d{2}( |-)*\d{3}$'),  # 2 dig - 3 dig
    u'PT': re.compile(r'\d{4}(-\d{3})?$'),  # 4 digits - 3 dig ???
    u'QA': re.compile(r'.+$'),  # no standard
    u'RE': re.compile(r'\d{5}$'),  # 5 digits
    u'RO': re.compile(r'\d{6}$'),  # 6 digits
    u'RS': re.compile(r'\d{5}$'),  # 5 digits
    u'RU': re.compile(r'\d{6}$'),  # 6 digits
    u'RW': re.compile(r'.+$'),  # no standard
    u'SA': re.compile(r'.+$'),  # to funny
    u'SE': re.compile(r'\d{3} *\d{2}$'),  # 3 dig 2 dig
    u'SG': re.compile(r'\d{2}$'),  # 2 digits
    u'SI': re.compile(r'\d{4}$'),  # 4 digits
    u'SK': re.compile(r'\d{3} *\d{2}$'),  # 3 dig 2 dig
    u'SN': re.compile(r'\d{5}$'),  # 5 digits
    u'TH': re.compile(r'\d{5}$'),  # 5 digits
    u'TN': re.compile(r'\d{4}$'),  # 4 digits
    u'TR': re.compile(r'\d{5}$'),  # 5 digits
    u'UG': re.compile(r'.+$'),  # no standard
    u'US': re.compile(r'\d{5}$'),  # 5 digits
    u'UY': re.compile(r'\d{5}$'),  # 5 digits
    u'VN': re.compile(r'\d{6}$'),  # 6 digits
    u'ZA': re.compile(r'\d{4}$'),  # 4 digits
}
