.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

===============================
collective.contact.importexport
===============================

.. image:: https://github.com/IMIO/collective.contact.importexport/actions/workflows/main.yml/badge.svg
    :target: https://github.com/IMIO/collective.contact.importexport/actions/workflows/main.yml

.. image:: https://coveralls.io/repos/github/IMIO/collective.contact.importexport/badge.svg
    :target: https://coveralls.io/github/IMIO/collective.contact.importexport

Import and export organizations and persons with csv files, there are 4 csv files:

- organizations
- persons
- positions (not yet managed)
- held_positions

! This is a WIP:

- Import is managed via a transmogrifier pipeline.
- Export can be managed with a collective.documentgenerator template. (not yet included in this product)

Features
--------

- Import from csv format. Text column must be enclosed with double quotes. A double quote in content must be escaped with another double quote.
- Organizations can be hierarchical: sub organizations can be defined.
- Held positions are linked to persons and organizations.
- Pipeline can contain other sections to manage new columns.

Examples of csv files
---------------------

 https://github.com/IMIO/collective.contact.importexport/blob/master/src/collective/contact/importexport/tests/data/organizations.csv

Documentation
-------------

Full documentation for end users can be found in the "docs" folder, and is also available online at http://docs.plone.org/foo/bar


Translations
------------

This product has been translated into

- French
- English


Installation
------------

Install collective.contact.importexport by adding it to your buildout::

    [buildout]

    ...

    eggs =
        collective.contact.importexport


and then running ``bin/buildout``


Versions
--------

- Version 2.x is for Plone 6.1+ only
- Version 1.x is for Plone 4


Contribute
----------

- Issue Tracker: https://github.com/IMIO/collective.contact.importexport/issues
- Source Code: https://github.com/IMIO/collective.contact.importexport


Support
-------

If you are having issues, please let us know in github issues tracker.


License
-------

The project is licensed under the GPLv2.
