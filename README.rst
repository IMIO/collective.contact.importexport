.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

===============================
collective.contact.importexport
===============================

Import and export organizations and persons with csv files, there are 4 csv files:
- organizations
- persons
- functions_file
- occupied_functions_file

! This is a WIP, only flat organizations can be imported for now.

Features
--------

- Import flat organizations list


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
