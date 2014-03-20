from django.db.migrations.state import ProjectState
from django.test import TestCase
from django.db import connection, IntegrityError, migrations, models
from uuidfield.fields import UUIDField


class UUIDFieldMigrationTestCase(TestCase):
    """
    UUIDField migration tests.

    Based on https://github.com/django/django/blob/master/tests/migrations/test_operations.py
    """

    def get_table_description(self, table):
        with connection.cursor() as cursor:
            return connection.introspection.get_table_description(cursor, table)

    def assertColumnExists(self, table, column):
        self.assertIn(column, [c.name for c in self.get_table_description(table)])

    def assertTableExists(self, table):
        with connection.cursor() as cursor:
            self.assertIn(table, connection.introspection.get_table_list(cursor))

    def assertTableNotExists(self, table):
        with connection.cursor() as cursor:
            self.assertNotIn(table, connection.introspection.get_table_list(cursor))

    def test_create_model(self):
        """
        Tests the CreateModel operation.
        """
        operation = migrations.CreateModel(
            "uuidmodel",
            [
                ("id", models.AutoField(primary_key=True)),
                ("uuid", UUIDField(auto=True)),
                ],
            )
        # Test the state alteration
        project_state = ProjectState()
        new_state = project_state.clone()
        operation.state_forwards("test_crmo", new_state)
        self.assertEqual(new_state.models["test_crmo", "uuidmodel"].name, "uuidmodel")
        self.assertEqual(len(new_state.models["test_crmo", "uuidmodel"].fields), 2)
        # Test the database alteration
        self.assertTableNotExists("test_crmo_uuidmodel")
        with connection.schema_editor() as editor:
            operation.database_forwards("test_crmo", editor, project_state, new_state)
        self.assertTableExists("test_crmo_uuidmodel")
        self.assertColumnExists("test_crmo_uuidmodel", "uuid")
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards("test_crmo", editor, new_state, project_state)
        self.assertTableNotExists("test_crmo_uuidmodel")
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "CreateModel")
        self.assertEqual(len(definition[1]), 2)
        self.assertEqual(len(definition[2]), 0)
        self.assertEqual(definition[1][0], "uuidmodel")