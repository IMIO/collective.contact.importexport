from collective.documentgenerator.helper.archetypes import ATDocumentGenerationHelperView
from plone import api


class DashboardDGBaseHelper():
    """
        Common methods
    """

    objs = []
    sel_type = ''

    def is_dashboard(self):
        """ Test if template is rendered from a dashboard """
        return 'facetedQuery' in self.request.form

    def uids_to_objs(self, brains):
        """ set objects from brains """
        # can be used like this in normal template:
        # do section- if view.is_dashboard()
        # do text if view.uids_to_objs(brains)
        self.objs = []
        for brain in brains:
            self.objs.append(brain.getObject())
        self.sel_type = len(brains) and self.objs[0].portal_type or ''
        return False


class DocumentGenerationDirectoryHelper(ATDocumentGenerationHelperView, DashboardDGBaseHelper):
    """
        Helper for collective.contact.core directory
    """

    def __init__(self, context, request):
        super(DocumentGenerationDirectoryHelper, self).__init__(context, request)
        self.uids = {}
        self.pers = {}
        self.directory_path = '/'.join(self.real_context.aq_parent.getPhysicalPath())
        self.dp_len = len(self.directory_path)

    def get_organizations(self):
        """
            Return a list of organizations, ordered by path, with parent id.
            [(id, parent_id, obj)]
        """
        lst = []
        id = 0
        paths = {}
        for brain in self.portal.portal_catalog(portal_type='organization', path=self.directory_path, sort_on='path'):
            id += 1
            self.uids[brain.UID] = id
            obj = brain.getObject()
            path = brain.getPath()[self.dp_len:]
            parts = path.split('/')
            p_path = '/'.join(parts[:-1])
            paths[path] = id
            if p_path:
                if paths.has_key(p_path):
                    p_id = paths[p_path]
                else:
                    p_id = 0
            lst.append((id, p_id, obj))
        return lst

    def get_persons(self):
        """
            Return a list of persons.
            [(id, obj)]
        """
        lst = []
        id = 0
        for brain in self.portal.portal_catalog(portal_type='person', path=self.directory_path,
                                                sort_on='sortable_title'):
            id += 1
            self.uids[brain.UID] = id
            self.pers[brain.getPath()[self.dp_len:]] = id
            obj = brain.getObject()
            lst.append((id, obj))
        return lst

    def get_held_positions(self):
        """
            Return a list of held positions tuples.
            [(id, person_id, org_id, obj)]
        """
        lst = []
        id = 0
        for brain in self.portal.portal_catalog(portal_type='held_position', path=self.directory_path, sort_on='path'):
            id += 1
            self.uids[brain.UID] = id
            obj = brain.getObject()
            # pers id
            path = brain.getPath()[self.dp_len:]
            parts = path.split('/')
            p_path = '/'.join(parts[:-1])
            p_id = self.pers[p_path]
            # org id
            org = obj.get_organization()
            org_id = ''
            if org:
                org_id = self.uids[org.UID()]
            lst.append((id, p_id, org_id, obj))
        return lst

    def get_formated_phone(self, contact, type_phone="cell_phone"):
        str_phones = ""
        if hasattr(contact, type_phone) and getattr(contact, type_phone) is not None:
            str_phones = ";".join(getattr(contact, type_phone))
        return str_phones


#    def is_internal(self, contact):
#        """
#            Check if contact is internal (not INotPloneGroupContact => IPloneGroupContact or IPers)
#        """
#        return 0 #not INotPloneGroupContact.providedBy(contact)
