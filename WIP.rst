===============================================
Import contacts through Transmogrifier Pipeline
===============================================


Use-case
--------

We need to be able to import contacts (organizations, persons, positions) into Plone.


Technical choices
-----------------

Contacts are store in 3 separate CSV files, and can depend on each other.
Thus, we need to have all the informations together, we cannot split the 3 csv into different pipelines or different csvsource blueprints.

We also need to create organization in the right order, parents first, and store the created objects UID to use it later for the children.
This information will be storer on a pipeline-wide annotation.

We also need to count lines to be able to raise a usable error message to the user.

As there can be more than one directory in the site, we will need to pass the path as a parameter.

Order of operations :
 1. import CSVs (status : done)
 2. remove first lines (status : done)
 3. create organization dependency (sorted) "graph" (status : done)
 4. check organization data (status : todo)
 5. create organization & store ID, path, UID in annotation (status : todo)
 6. check contact data (status : todo)
 7. create contact & store ID, UID in annotation (status : todo)
 8. create positions (status : todo)

Todo :
 - import of organizations types
 - update of existing contents

Limitations
-----------

We don't handle the change of parent for an organization or a contact.


Usage
-----

The import pipeline is stored in portal_registry/edit/collective.contact.importexport.pipeline
It is immediately replicated on the FileSystem when changed.

The import pipeline can be executed via :
 bin/instance run src/collective/contact/importexport/scripts/execute_pipeline.py pipeline.cfg plone

where `plone` is the Plone site id.
