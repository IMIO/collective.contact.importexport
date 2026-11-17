*** Settings ***
Documentation  collective.contact.importexport keywords, built on the ui_plone${PLONE_MAJOR}.robot keywords.
...            Robot Framework 3 syntax (shared with the Plone 4.3 environment).
...            Fixture: collective.contact.core test data (mydirectory) and the default registry pipeline.
...            The registry record edit form (z3c.form ids) is the same in Plone 4 and 6.
Resource  ui_plone${PLONE_MAJOR}.robot
Library  OperatingSystem
Library  String


*** Variables ***
${DIRECTORY_URL}  ${PLONE_URL}/mydirectory
${PIPELINE_RECORD}  collective.contact.importexport.interfaces.IPipelineConfiguration.pipeline
${PIPELINE_FIELD}  css=#form-widgets-value
${ORGANIZATIONS}  SEPARATOR=\n
...  id,id_parent,title,description,activity,use_parent_address,street,number,additional_address_details,zip_code,city,phone,cell_phone,fax,email,website,region,country,uid
...  1,,IMIO,Intercommunale de Mutualisation Informatique et Organisationnelle,Intercommunale,False,Rue Léon Morel,1,,5032,Isnes,081/586.100,,,contact@imio.be,https://www.imio.be,,Belgique,
${PERSONS}  SEPARATOR=\n
...  id,lastname,firstname,gender,person_title,birthday,use_parent_address,street,number,additional_address_details,zip_code,city,phone,cell_phone,fax,email,website,region,country,uid
...  1,Dupont,Jean,M,Monsieur,1975/04/12,False,Rue de Fer,25,,5000,Namur,,,,jean.dupont@example.com,,,Belgique,
${HELD_POSITIONS}  id,id_person,id_organization,id_function,label,start_date,end_date,use_parent_address,street,number,additional_address_details,zip_code,city,phone,cell_phone,fax,email,website,region,country,uid


*** Keywords ***
Open a manager browser
    Open test browser
    Set window size  1280  2000
    Enable autologin as  Manager

Open the pipeline record
    Go to  ${PLONE_URL}/portal_registry/edit/${PIPELINE_RECORD}
    Wait until page contains element  ${PIPELINE_FIELD}

Replace in the pipeline
    [Documentation]  Edits the pipeline record. Arguments: old text, new text, old text, new text...
    [Arguments]  @{replacements}
    Open the pipeline record
    ${pipeline}=  Get value  ${PIPELINE_FIELD}
    FOR  ${old}  ${new}  IN  @{replacements}
        Should contain  ${pipeline}  ${old}
        ${pipeline}=  Replace string  ${pipeline}  ${old}  ${new}
    END
    Input text  ${PIPELINE_FIELD}  ${pipeline}
    Click button  css=#form-buttons-save

Create the import files
    [Documentation]  csv files named as in the default pipeline, in a new temporary directory
    ${dir}=  Evaluate  tempfile.mkdtemp()  modules=tempfile
    Set test variable  ${IMPORT_DIR}  ${dir}
    Create file  ${dir}/organizations-test.csv  ${ORGANIZATIONS}\n  encoding=UTF-8
    Create file  ${dir}/persons-test.csv  ${PERSONS}\n  encoding=UTF-8
    Create file  ${dir}/heldpositions-test.csv  ${HELD_POSITIONS}\n  encoding=UTF-8

Remove the import files
    Remove directory  ${IMPORT_DIR}  recursive=True

Run the import
    [Documentation]  Called as a link built by Plone (CSRF token). The view answers 204 (no content):
    ...              a browser would stay on its page.
    Go to  ${PLONE_URL}
    ${token}=  Get the CSRF token
    ${status}=  Execute javascript  var request = new XMLHttpRequest();
    ...  request.open('GET', '${PLONE_URL}/@@execute-contact-pipeline?_authenticator=${token}', false);
    ...  request.send(); return request.status;
    Should be equal as integers  ${status}  204

The import summary contains
    [Arguments]  ${text}
    ${summary}=  Get file  ${IMPORT_DIR}/ie_shortlog.log  encoding=UTF-8
    Should contain  ${summary}  ${text}
