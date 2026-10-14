*** Settings ***
Documentation  Import of contacts with the pipeline of the configuration registry (execute-contact-pipeline view).
...            Version-independent: Plone selectors are in ui_plone*.robot.
Resource  importexport.robot
Test Setup  Open a manager browser
Test Teardown  Close all browsers


*** Test Cases ***
A manager edits the import pipeline in the configuration registry
    Replace in the pipeline  csv_encoding =  csv_encoding = utf8
    Wait until location is  ${PLONE_URL}/portal_registry
    Open the pipeline record
    Textarea should contain  ${PIPELINE_FIELD}  csv_encoding = utf8

A manager imports contacts with the execute-contact-pipeline view
    Create the import files
    Replace in the pipeline  basepath =  basepath = ${IMPORT_DIR}  subpath = imports  subpath =
    ...  csv_encoding =  csv_encoding = utf8
    Run the import
    Go to  ${DIRECTORY_URL}/imio
    Page should contain  Intercommunale de Mutualisation Informatique et Organisationnelle
    Page should contain  contact@imio.be
    Go to  ${DIRECTORY_URL}/jean-dupont
    Page should contain  jean.dupont@example.com
    The import summary contains  'O' => (nb=1, N=1, U=0, D=0, e=0), 'P' => (nb=1, N=1, U=0, D=0, e=0)
    [Teardown]  Run keywords  Remove the import files  AND  Close all browsers
