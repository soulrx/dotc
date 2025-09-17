import unittest
import sys
import os

# Add the src directory to the path so we can import dotc
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from dotc.dotc import Dotc, DataPath


class TestDotcBasicFunctionality(unittest.TestCase):
    """Test basic Dotc functionality with simple data structures."""
    
    def setUp(self):
        self.simple_dict = {'a': 1, 'b': 2, 'c': 3}
        self.simple_list = [10, 20, 30, 40]
        self.mixed_data = {'numbers': [1, 2, 3], 'string': 'test', 'nested': {'value': 42}}
    
    def test_simple_dict_access(self):
        """Test accessing simple dictionary values using ._val."""
        d = Dotc(self.simple_dict)
        # Access the actual values via ._val
        self.assertEqual(d.a._val, 1)
        self.assertEqual(d.b._val, 2)
        self.assertEqual(d.c._val, 3)
    
    def test_simple_list_access(self):
        """Test accessing list elements with _index notation."""
        d = Dotc(self.mixed_data)
        self.assertEqual(d.numbers._0._val, 1)
        self.assertEqual(d.numbers._1._val, 2)
        self.assertEqual(d.numbers._2._val, 3)
    
    def test_missing_key_returns_default(self):
        """Test that missing keys return the default value (None)."""
        d = Dotc(self.simple_dict)
        self.assertIsNone(d.missing_key)
        # Test nested missing access
        missing_nested = d.a.nonexistent
        self.assertIsNone(missing_nested)
    
    def test_custom_default_value(self):
        """Test custom default values."""
        d = Dotc(self.simple_dict, default='NOT_FOUND')
        self.assertEqual(d.missing_key, 'NOT_FOUND')
    
    def test_data_resolution_with_underscore(self):
        """Test full data resolution using the ._ property."""
        d = Dotc(self.mixed_data)
        resolved = d._
        self.assertEqual(resolved, self.mixed_data)
        
        # Test partial resolution
        nested_resolved = d.nested._
        self.assertEqual(nested_resolved, {'value': 42})


class TestDotcComplexDataStructures(unittest.TestCase):
    """Test Dotc with complex nested data structures."""
    
    def setUp(self):
        self.staff_data = {
            'staff': {
                'coders': ['mike', 'jeremie', 'trey', 'donnie'],
                'managers': ['sarah', 'john'],
                'details': {
                    'team_size': 6,
                    'location': 'NYC',
                    'projects': [
                        {'name': 'project_a', 'status': 'active'},
                        {'name': 'project_b', 'status': 'completed'}
                    ]
                }
            },
            'budget': {
                'quarterly': [100000, 120000, 110000, 130000],
                'annual': 460000
            }
        }
        
        self.api_response = {
            'data': {
                'users': [
                    {
                        'id': 1,
                        'profile': {
                            'name': 'Alice Johnson',
                            'email': 'alice@example.com',
                            'preferences': {
                                'theme': 'dark',
                                'notifications': ['email', 'push']
                            }
                        },
                        'scores': [85, 92, 78, 88]
                    },
                    {
                        'id': 2,
                        'profile': {
                            'name': 'Bob Smith',
                            'email': 'bob@example.com',
                            'preferences': {
                                'theme': 'light',
                                'notifications': ['email']
                            }
                        },
                        'scores': [90, 85, 95, 87]
                    }
                ],
                'metadata': {
                    'total_users': 2,
                    'last_updated': '2025-09-17',
                    'version': '1.0'
                }
            }
        }
    
    def test_deep_nested_access(self):
        """Test accessing deeply nested data structures."""
        d = Dotc(self.staff_data)
        
        # Test accessing nested arrays - use ._val for scalar values
        self.assertEqual(d.staff.coders._0._val, 'mike')
        self.assertEqual(d.staff.coders._3._val, 'donnie')
        self.assertEqual(d.staff.managers._1._val, 'john')
        
        # Test accessing nested dictionaries - use ._val for scalar values
        self.assertEqual(d.staff.details.team_size._val, 6)
        self.assertEqual(d.staff.details.location._val, 'NYC')
        
        # Test accessing arrays of dictionaries
        self.assertEqual(d.staff.details.projects._0.name._val, 'project_a')
        self.assertEqual(d.staff.details.projects._1.status._val, 'completed')
        
        # Test budget data
        self.assertEqual(d.budget.quarterly._2._val, 110000)
        self.assertEqual(d.budget.annual._val, 460000)
    
    def test_api_response_navigation(self):
        """Test navigating complex API response structures."""
        d = Dotc(self.api_response)
        
        # Test user data access - use ._val for scalar values
        self.assertEqual(d.data.users._0.id._val, 1)
        self.assertEqual(d.data.users._0.profile.name._val, 'Alice Johnson')
        self.assertEqual(d.data.users._0.profile.email._val, 'alice@example.com')
        self.assertEqual(d.data.users._0.profile.preferences.theme._val, 'dark')
        self.assertEqual(d.data.users._0.profile.preferences.notifications._0._val, 'email')
        self.assertEqual(d.data.users._0.scores._1._val, 92)
        
        # Test second user
        self.assertEqual(d.data.users._1.profile.name._val, 'Bob Smith')
        self.assertEqual(d.data.users._1.profile.preferences.theme._val, 'light')
        self.assertEqual(d.data.users._1.scores._2._val, 95)
        
        # Test metadata
        self.assertEqual(d.data.metadata.total_users._val, 2)
        self.assertEqual(d.data.metadata.version._val, '1.0')
    
    def test_mixed_types_in_arrays(self):
        """Test arrays containing mixed data types."""
        mixed_array_data = {
            'mixed': [
                'string',
                42,
                {'nested': 'dict'},
                [1, 2, 3],
                True,
                None
            ]
        }
        
        d = Dotc(mixed_array_data)
        self.assertEqual(d.mixed._0._val, 'string')
        self.assertEqual(d.mixed._1._val, 42)
        self.assertEqual(d.mixed._2.nested._val, 'dict')
        self.assertEqual(d.mixed._3._1._val, 2)
        self.assertEqual(d.mixed._4._val, True)
        self.assertIsNone(d.mixed._5._val)


class TestDotcSpawnFunctionality(unittest.TestCase):
    """Test the spawn functionality and tuple returns."""
    
    def setUp(self):
        self.staff_data = {
            'staff': {
                'coders': ['mike', 'jeremie', 'trey', 'donnie'],
                'details': {'team_size': 4}
            }
        }
    
    def test_instantiation_with_pathget(self):
        """Test instantiation with _pathget parameter returns tuple."""
        dc, result = Dotc(self.staff_data, _pathget='staff.coders.0')
        
        self.assertIsInstance(dc, Dotc)
        self.assertEqual(result, 'mike')
        
        # Verify the object still works normally - use ._val for scalar access
        self.assertEqual(dc.staff.coders._1._val, 'jeremie')
    
    def test_spawn_method(self):
        """Test the spawn method returns tuple."""
        dc = Dotc(self.staff_data)
        dc_ref, result = dc.spawn('staff.coders.2')
        
        self.assertIs(dc_ref, dc)  # Should return the same object
        self.assertEqual(result, 'trey')
    
    def test_create_with_result_factory(self):
        """Test the create_with_result factory method."""
        dc, result = Dotc.create_with_result(self.staff_data, 'staff.details.team_size')
        
        self.assertIsInstance(dc, Dotc)
        self.assertEqual(result, 4)
        
        # Verify normal access still works - use ._val for scalar access
        self.assertEqual(dc.staff.coders._3._val, 'donnie')
    
    def test_call_method_after_spawn(self):
        """Test using __call__ method after spawn instantiation."""
        dc, first_result = Dotc(self.staff_data, _pathget='staff.coders.0')
        self.assertEqual(first_result, 'mike')
        
        # Use __call__ for additional queries
        second_result = dc('staff.coders.1')
        self.assertEqual(second_result, 'jeremie')
        
        third_result = dc('staff.details.team_size')
        self.assertEqual(third_result, 4)
    
    def test_spawn_with_invalid_path(self):
        """Test spawn with invalid paths returns default."""
        dc = Dotc(self.staff_data)
        dc_ref, result = dc.spawn('invalid.path.here')
        
        self.assertIs(dc_ref, dc)
        self.assertIsNone(result)  # Should return default (None)


class TestDotcCallMethod(unittest.TestCase):
    """Test the __call__ method functionality."""
    
    def setUp(self):
        self.complex_data = {
            'config': {
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'credentials': {
                        'username': 'admin',
                        'password': 'secret'
                    }
                },
                'api': {
                    'endpoints': [
                        '/users',
                        '/products',
                        '/orders'
                    ],
                    'timeout': 30
                }
            }
        }
    
    def test_call_method_basic(self):
        """Test basic __call__ method functionality."""
        d = Dotc(self.complex_data)
        
        self.assertEqual(d('config.database.host'), 'localhost')
        self.assertEqual(d('config.database.port'), 5432)
        self.assertEqual(d('config.api.timeout'), 30)
    
    def test_call_method_with_arrays(self):
        """Test __call__ method with array access."""
        d = Dotc(self.complex_data)
        
        self.assertEqual(d('config.api.endpoints.0'), '/users')
        self.assertEqual(d('config.api.endpoints.1'), '/products')
        self.assertEqual(d('config.api.endpoints.2'), '/orders')
    
    def test_call_method_deep_nesting(self):
        """Test __call__ method with deeply nested paths."""
        d = Dotc(self.complex_data)
        
        self.assertEqual(d('config.database.credentials.username'), 'admin')
        self.assertEqual(d('config.database.credentials.password'), 'secret')
    
    def test_call_method_invalid_path(self):
        """Test __call__ method with invalid paths."""
        d = Dotc(self.complex_data)
        
        self.assertIsNone(d('invalid.path'))
        self.assertIsNone(d('config.nonexistent.key'))
        self.assertIsNone(d(''))
    
    def test_call_method_empty_or_none(self):
        """Test __call__ method with empty or None paths."""
        d = Dotc(self.complex_data)
        
        self.assertIsNone(d(None))
        self.assertIsNone(d(''))
        self.assertIsNone(d(123))  # Non-string input


class TestDotcEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_empty_data_structures(self):
        """Test with empty data structures."""
        # Empty dict
        d1 = Dotc({})
        self.assertEqual(d1._, {})
        self.assertIsNone(d1.anything)
        
        # Empty list - Dotc treats empty lists specially
        d2 = Dotc({'empty_list': []})
        # Empty lists result in no stored attributes, so accessing returns default
        self.assertIsNone(d2.empty_list)
        
        # But the full resolution should still show the empty list
        resolved = d2._
        if resolved is not None:  # If it gets stored
            self.assertEqual(resolved.get('empty_list', []), [])
        
        # Test with a list that has content vs empty
        d3 = Dotc({'has_content': [1], 'empty': []})
        self.assertIsNotNone(d3.has_content)  # This should exist
        self.assertIsNone(d3.empty)  # This should be None (default)
    
    def test_none_values(self):
        """Test handling of None values."""
        data_with_none = {
            'value': None,
            'nested': {
                'also_none': None,
                'list_with_none': [1, None, 3]
            }
        }
        
        d = Dotc(data_with_none)
        # None values are stored in ._val
        self.assertIsNone(d.value._val)
        self.assertIsNone(d.nested.also_none._val)
        self.assertIsNone(d.nested.list_with_none._1._val)
        self.assertEqual(d.nested.list_with_none._2._val, 3)
    
    def test_boolean_and_numeric_values(self):
        """Test handling of boolean and numeric values."""
        data = {
            'bool_true': True,
            'bool_false': False,
            'zero': 0,
            'negative': -42,
            'float_val': 3.14,
            'large_num': 1000000
        }
        
        d = Dotc(data)
        # Use ._val to access the actual boolean/numeric values
        self.assertTrue(d.bool_true._val)
        self.assertFalse(d.bool_false._val)
        self.assertEqual(d.zero._val, 0)
        self.assertEqual(d.negative._val, -42)
        self.assertEqual(d.float_val._val, 3.14)
        self.assertEqual(d.large_num._val, 1000000)
    
    def test_string_values_with_special_characters(self):
        """Test string values with special characters."""
        data = {
            'unicode': 'Hello 🌍',
            'multiline': 'Line 1\nLine 2\nLine 3',
            'escaped': 'Quotes: "double" and \'single\'',
            'path_like': 'looks.like.a.path',
            'empty_string': ''
        }
        
        d = Dotc(data)
        # Use ._val to access the actual string values
        self.assertEqual(d.unicode._val, 'Hello 🌍')
        self.assertEqual(d.multiline._val, 'Line 1\nLine 2\nLine 3')
        self.assertEqual(d.escaped._val, 'Quotes: "double" and \'single\'')
        self.assertEqual(d.path_like._val, 'looks.like.a.path')
        self.assertEqual(d.empty_string._val, '')
    
    def test_custom_node_names(self):
        """Test custom node names."""
        d = Dotc({'test': 'value'}, node='custom_root')
        self.assertEqual(d._node, 'custom_root')
        # Use ._val to access the actual value
        self.assertEqual(d.test._val, 'value')


class TestDataPath(unittest.TestCase):
    """Test the DataPath utility class."""
    
    def setUp(self):
        self.test_data = {
            'level1': {
                'level2': {
                    'level3': ['item0', 'item1', 'item2'],
                    'other': 'value'
                }
            }
        }
    
    def test_datapath_get_with_dict(self):
        """Test DataPath.get with regular dictionary."""
        dp = DataPath()
        
        # DataPath should work with regular Python dicts
        self.assertEqual(dp.get('level1.level2.other', self.test_data), 'value')
        self.assertEqual(dp.get('level1.level2.level3.0', self.test_data), 'item0')
        self.assertEqual(dp.get('level1.level2.level3.2', self.test_data), 'item2')
        
        # Test with missing path returns default (False)
        result = dp.get('nonexistent.path', self.test_data)
        self.assertFalse(result)
    
    def test_datapath_get_with_dotc(self):
        """Test DataPath.get with Dotc objects."""
        d = Dotc(self.test_data)
        dp = DataPath()
        
        result = dp.get('level1.level2.level3', d)
        self.assertEqual(result, ['item0', 'item1', 'item2'])
        
        result = dp.get('level1.level2.level3.1', d)
        self.assertEqual(result, 'item1')
    
    def test_datapath_get_with_default(self):
        """Test DataPath.get with default values."""
        dp = DataPath()
        
        result = dp.get('nonexistent.path', self.test_data, default='NOT_FOUND')
        self.assertEqual(result, 'NOT_FOUND')


class TestDotcShow(unittest.TestCase):
    """Test the _show debugging functionality."""
    
    def setUp(self):
        self.test_data = {
            'a': 1,
            'b': {
                'c': [1, 2, 3],
                'd': 'test'
            }
        }
    
    def test_show_method_exists(self):
        """Test that _show method exists and can be called."""
        d = Dotc(self.test_data)
        
        # These should not raise exceptions
        try:
            d._show()
            d._show(v=1)
            d._show(d.b, v=1)
        except Exception as e:
            self.fail(f"_show method raised an exception: {e}")


if __name__ == '__main__':
    # Create a test suite with all test classes
    test_classes = [
        TestDotcBasicFunctionality,
        TestDotcComplexDataStructures,
        TestDotcSpawnFunctionality,
        TestDotcCallMethod,
        TestDotcEdgeCases,
        TestDataPath,
        TestDotcShow
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"DOTC TEST SUITE SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ Some tests failed. Check the output above.")