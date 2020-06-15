#!/bin/bash
# i18ndude should be available in current $PATH (eg by running
# ``export PATH=$PATH:$BUILDOUT_DIR/bin`` when i18ndude is located in your buildout's bin directory)
#
# For every language you want to translate into you need a
# locales/[language]/LC_MESSAGES/collective.contact.importexport.po
# (e.g. locales/de/LC_MESSAGES/collective.contact.importexport.po)

domain=collective.contact.importexport

i18ndude rebuild-pot --pot $domain.pot --create $domain ../
i18ndude sync --pot $domain.pot */LC_MESSAGES/$domain.po

# Files to_pycountry.po and to_pycountry_lower.po are particular.
# There are no common ids between languages
# The id is the local language string and the translated string is always english
# to_pycountry_lower.po is used in common_input_checks section to use country name to validate phone
