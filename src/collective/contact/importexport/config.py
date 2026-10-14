import re


ANNOTATION_KEY = "collective.contact.importexport"

ZIP_DIGIT = [
    "AT",
    "AU",
    "BE",
    "BG",
    "CH",
    "CN",
    "CY",
    "DE",
    "DK",
    "DZ",
    "EE",
    "ES",
    "FI",
    "FR",
    "GF",
    "GP",
    "HR",
    "HU",
    "ID",
    "IL",
    "IN",
    "IS",
    "IT",
    "JO",
    "KE",
    "KR",
    "KW",
    "KZ",
    "LK",
    "LU",
    "LV",
    "LT",
    "MC",
    "MD",
    "MG",
    "MU",
    "MX",
    "MY",
    "MZ",
    "NC",
    "NO",
    "NZ",
    "PH",
    "RE",
    "RO",
    "RS",
    "RU",
    "SG",
    "SI",
    "SN",
    "TH",
    "TN",
    "TR",
    "US",
    "UY",
    "VN",
    "ZA",
]
# Based on https://en.wikipedia.org/wiki/List_of_postal_codes
ZIP_PATTERN = {
    "AD": re.compile(r"(AD)?\d{3}$"),  # 3 digits
    "AE": re.compile(r".+$"),  # no standard
    "AR": re.compile(r"(\d{4}|\w\d{4}|\w\d{4}\w{3})$"),  # 4 digits or ...
    "AT": re.compile(r"\d{4}$"),  # 4 digits
    "AU": re.compile(r"\d{4}$"),  # 4 digits
    "BE": re.compile(r"\d{4}$"),  # 4 digits
    "BF": re.compile(r".+$"),  # no standard
    "BG": re.compile(r"\d{4}$"),  # 4 digits
    "BM": re.compile(r".+$"),  # no standard
    "BR": re.compile(r"\d{5}( |-)\d{3}$"),  # 5 dig - 3 dig
    "BW": re.compile(r".+$"),  # no standard
    "CA": re.compile(r"\w{3} *\w{3}$"),  # 3 chars 3 chars
    "CD": re.compile(r".+$"),  # no standard
    "CG": re.compile(r".+$"),  # no standard
    "CH": re.compile(r"\d{4}$"),  # 4 digits
    "CI": re.compile(r".+$"),  # no standard
    "CN": re.compile(r"\d{6}$"),  # 6 digits
    "CY": re.compile(r"\d{4}$"),  # 4 digits
    "CZ": re.compile(r"\d{3} *\d{2}$"),  # 3 dig 2 dig
    "DE": re.compile(r"\d{5}$"),  # 5 digits
    "DK": re.compile(r"\d{4}$"),  # 4 digits
    "DZ": re.compile(r"\d{5}$"),  # 5 digits
    "EE": re.compile(r"\d{5}$"),  # 5 digits
    "ES": re.compile(r"\d{5}$"),  # 5 digits
    "FI": re.compile(r"\d{5}$"),  # 5 digits
    "FR": re.compile(r"\d{5}$"),  # 5 digits
    "GB": re.compile(r".+$"),  # to funny
    "GF": re.compile(r"\d{5}$"),  # 5 digits
    "GG": re.compile(r".+$"),  # to funny
    "GI": re.compile(r".+$"),  # to funny
    "GP": re.compile(r"\d{5}$"),  # 5 digits
    "GR": re.compile(r"\d{3} *\d{2}$"),  # 3 dig 2 dig
    "HK": re.compile(r".+$"),  # no standard
    "HR": re.compile(r"\d{5}$"),  # 5 digits
    "HU": re.compile(r"\d{4}$"),  # 4 digits
    "ID": re.compile(r"\d{5}$"),  # 5 digits
    "IE": re.compile(r".+$"),  # to funny
    "IL": re.compile(r"\d{5}(\d{2})$"),  # 5 or 7 digits
    "IN": re.compile(r"\d{6}$"),  # 6 digits
    "IS": re.compile(r"\d{3}$"),  # 3 digits
    "IT": re.compile(r"\d{5}$"),  # 5 digits
    "JO": re.compile(r"\d{5}$"),  # 5 digits
    "JP": re.compile(r"\d{3}( *|-)\d{4}$"),  # 3 dig - 4 dig
    "KE": re.compile(r"\d{5}$"),  # 5 digits
    "KW": re.compile(r"\d{5}$"),  # 5 digits
    "KR": re.compile(r"\d{5}$"),  # 5 digits
    "KZ": re.compile(r"\d{6}$"),  # 6 digits
    "LB": re.compile(r"(\d{5}|\d{4} *\d{4})$"),  # 5 dig or 4 4
    "LK": re.compile(r"\d{5}$"),  # 5 digits
    "LU": re.compile(r"\d{4}$"),  # 4 digits
    "LV": re.compile(r"\d{4}$"),  # 4 digits
    "LT": re.compile(r"\d{5}$"),  # 5 digits
    "MA": re.compile(r"\d{2} *\d{3}$"),  # 5 digits with spaces
    "MC": re.compile(r"980\d{2}$"),  # 5 digits
    "MD": re.compile(r"\d{4}$"),  # 4 digits
    "MG": re.compile(r"\d{3}$"),  # 3 digits
    "MU": re.compile(r"\d{5}$"),  # 5 digits
    "MX": re.compile(r"\d{5}$"),  # 5 digits
    "MY": re.compile(r"\d{5}$"),  # 5 digits
    "MZ": re.compile(r"\d{4}$"),  # 4 digits
    "MT": re.compile(r"\w{3} *\d{4}$"),  # 3 chars 4 digits
    "NC": re.compile(r"988\d{2}$"),  # 5 digits
    "NL": re.compile(r"\d{4}( *\w{2})?$"),  # 4 digits 2 letters?
    "NO": re.compile(r"\d{4}$"),  # 4 digits
    "NZ": re.compile(r"\d{4}$"),  # 4 digits
    "PH": re.compile(r"\d{3,4}$"),  # 3 or 4 digits
    "PL": re.compile(r"\d{2}( |-)*\d{3}$"),  # 2 dig - 3 dig
    "PT": re.compile(r"\d{4}(-\d{3})?$"),  # 4 digits - 3 dig ???
    "QA": re.compile(r".+$"),  # no standard
    "RE": re.compile(r"\d{5}$"),  # 5 digits
    "RO": re.compile(r"\d{6}$"),  # 6 digits
    "RS": re.compile(r"\d{5}$"),  # 5 digits
    "RU": re.compile(r"\d{6}$"),  # 6 digits
    "RW": re.compile(r".+$"),  # no standard
    "SA": re.compile(r".+$"),  # to funny
    "SE": re.compile(r"\d{3} *\d{2}$"),  # 3 dig 2 dig
    "SG": re.compile(r"\d{2}$"),  # 2 digits
    "SI": re.compile(r"\d{4}$"),  # 4 digits
    "SK": re.compile(r"\d{3} *\d{2}$"),  # 3 dig 2 dig
    "SN": re.compile(r"\d{5}$"),  # 5 digits
    "TH": re.compile(r"\d{5}$"),  # 5 digits
    "TN": re.compile(r"\d{4}$"),  # 4 digits
    "TR": re.compile(r"\d{5}$"),  # 5 digits
    "UG": re.compile(r".+$"),  # no standard
    "US": re.compile(r"\d{5}$"),  # 5 digits
    "UY": re.compile(r"\d{5}$"),  # 5 digits
    "VN": re.compile(r"\d{6}$"),  # 6 digits
    "ZA": re.compile(r"\d{4}$"),  # 4 digits
}
