# -*- coding: utf-8 -*-

import re

ZIP_DIGIT = [u'BE', u'CH', u'CN', u'DE', u'DK', u'ES', u'FI', u'FR', u'HR', u'HU', u'IT', u'LU', u'LV', u'LT', u'MD',
             u'NL', u'RE', u'US']
ZIP_PATTERN = {
    u'BE': re.compile(r'\d{4}$'),  # 4 digits
    u'BR': re.compile(r'\d{5}( |-)\d{3}$'),  # 5 dig - 3 dig
    u'CA': re.compile(r'\w{3} *\w{3}$'),  # 3 chars 3 chars
    u'CH': re.compile(r'\d{4}$'),  # 4 digits
    u'CN': re.compile(r'\d{6}$'),  # 6 digits
    u'CZ': re.compile(r'\d{3} *\d{2}$'),  # 3 dig 2 dig
    u'DE': re.compile(r'\d{5}$'),  # 5 digits
    u'DK': re.compile(r'\d{4}$'),  # 4 digits
    u'ES': re.compile(r'\d{5}$'),  # 5 digits
    u'FI': re.compile(r'\d{5}$'),  # 5 digits
    u'FR': re.compile(r'\d{5}$'),  # 5 digits
    u'GB': re.compile(r'.+$'),  # trop bizarre
    u'HR': re.compile(r'\d{5}$'),  # 5 digits
    u'HU': re.compile(r'\d{4}$'),  # 4 digits
    u'IT': re.compile(r'\d{5}$'),  # 5 digits
    u'LU': re.compile(r'\d{4}$'),  # 4 digits
    u'LV': re.compile(r'\d{4}$'),  # 4 digits
    u'LT': re.compile(r'\d{5}$'),  # 5 digits
    u'MA': re.compile(r'\d{2} *\d{3}$'),  # 5 digits avec espace
    u'MD': re.compile(r'\d{4}$'),  # 4 digits
    u'NL': re.compile(r'\d{4}$'),  # 4 digits
    u'PT': re.compile(r'\d{4}(-\d{3})?$'),  # 4 digits - 3 dig ???
    u'RE': re.compile(r'\d{5}$'),  # 5 digits
    u'US': re.compile(r'\d{5}$'),  # 5 digits
}
