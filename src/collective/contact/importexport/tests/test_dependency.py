from collective.contact.importexport.blueprints.dependency import DependencySorter
from collective.contact.importexport.tests.base import PipelineTestCase


class TestDependencySorter(PipelineTestCase):

    def test_dependency_sorter(self):
        # children are given before their parents
        organizations = [
            {'_id': '3', '_oid': '2', 'title': u'Sub service', 'organization_type': u'Cellule'},
            {'_id': '2', '_oid': '1', 'title': u'Service', 'organization_type': u'Service', 'description': u''},
            {'_id': '1', 'title': u'Commune', 'organization_type': u'Commune', 'city': u'Namur'},
        ]
        persons = [{'_id': '1', 'lastname': u'Dupont', 'firstname': u'Jean'}]
        held_positions = [{'_id': '1', '_pid': '1', '_oid': '1', 'label': u'Mayor'}]
        items = self.run_pipeline(last_section='dependencysorter', organizations=organizations, persons=persons,
                                  held_positions=held_positions)
        # directory is updated with the new organization types and levels
        directory_item = items[0]
        self.assertEqual((directory_item['_type'], directory_item['_act'], directory_item['_set']),
                         ('directory', 'update', 'all'))
        self.assertEqual(directory_item['_path'], 'mydirectory')
        self.assertIn({'name': u'Commune', 'token': u'commune'}, directory_item['organization_types'])
        self.assertIn({'name': u'Cellule', 'token': u'cellule'}, directory_item['organization_levels'])
        # organizations are sorted by level, then persons, then held positions
        self.assertEqual([(item['_type'], item['_id']) for item in items[1:]],
                         [('organization', '1'), ('organization', '2'), ('organization', '3'), ('person', '1'),
                          ('held_position', '1')])
        self.assertEqual([item['_level'] for item in items[1:4]], [1, 2, 3])
        # empty values are set to None, except description and technical ones
        self.assertIsNone(items[1]['street'])
        self.assertEqual(items[1]['city'], u'Namur')
        self.assertEqual(items[2]['description'], u'')
        self.assertEqual(items[2]['_uid'], u'')
        self.assertIsNone(items[2]['website'])

    def test_get_level(self):
        sorter = DependencySorter.__new__(DependencySorter)
        relations = {'3': '2', '2': '1'}
        self.assertEqual(sorter.get_level(relations, '1'), 1)
        self.assertEqual(sorter.get_level(relations, '3'), 3)

    def test_ancestors(self):
        sorter = DependencySorter.__new__(DependencySorter)
        relations = {'3': '2', '2': '1'}
        self.assertEqual(sorter.ancestors(relations, '3'), ['1', '2', '3'])
        self.assertEqual(sorter.ancestors(relations, '1'), ['1'])
