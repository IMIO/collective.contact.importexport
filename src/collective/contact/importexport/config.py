# -*- coding: utf-8 -*-

import re

ZIP_DIGIT = [u'BE', u'FR']
ZIP_PATTERN = {
    u'BE': re.compile(r'\d{4}$'),  # 4 digits
    u'FR': re.compile(r'\d{5}$'),  # 5 digits
}
