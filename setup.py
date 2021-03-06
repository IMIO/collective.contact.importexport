# -*- coding: utf-8 -*-
"""Installer for the collective.contact.importexport package."""

from setuptools import find_packages
from setuptools import setup


long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CONTRIBUTORS.rst').read(),
    open('CHANGES.rst').read(),
])


setup(
    name='collective.contact.importexport',
    version='1.0.0.dev0',
    description="An add-on for Plone for collective.contact suite",
    long_description=long_description,
    # Get more from https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords='Python Plone',
    author='Benoit Suttor',
    author_email='bsuttor@imio.be',
    url='https://pypi.python.org/pypi/collective.contact.importexport',
    license='GPL version 2',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['collective', 'collective.contact'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'collective.contact.core',
        'collective.transmogrifier',
        'future',
        'imio.helpers>=0.40',
        'imio.pyutils',
        'ipdb',
        'phonenumbers',
        'plone.api',
        'plone.app.transmogrifier',
        'Products.GenericSetup>=1.8.2',
        'pycountry',
        'setuptools',
        'transmogrify.dexterity',
    ],
    extras_require={
        'test': [
            'collective.taxonomy',
            'plone.app.testing',
            # Plone KGS does not use this version, because it would break
            # Remove if your package shall be part of coredev.
            # plone_coredev tests as of 2016-04-01.
            'plone.testing',
            'plone.app.contenttypes',
            'plone.app.robotframework[debug]',
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
