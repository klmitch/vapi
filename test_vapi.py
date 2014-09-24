# Copyright 2014 Rackspace
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the
#    License. You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing,
#    software distributed under the License is distributed on an "AS
#    IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
#    express or implied. See the License for the specific language
#    governing permissions and limitations under the License.

import functools
import unittest

import mock

import vapi


class RequiredTest(unittest.TestCase):
    def test_init(self):
        req = vapi.Required(5, set(['caps']))

        self.assertEqual(req.since, 5)
        self.assertEqual(req.caps, set(['caps']))

    def test_required_old(self):
        req = vapi.Required(5, None)

        result = req.required(3, set(['a', 'b', 'c']))

        self.assertFalse(result)

    def test_required_cap_optional(self):
        req = vapi.Required(5, set(['b']))

        result = req.required(5, set(['a', 'c']))

        self.assertFalse(result)

    def test_required_nocap(self):
        req = vapi.Required(5, None)

        result = req.required(5, set(['a', 'b', 'c']))

        self.assertTrue(result)

    def test_required_withcap(self):
        req = vapi.Required(5, set(['b']))

        result = req.required(5, set(['a', 'b', 'c']))

        self.assertTrue(result)


class ProvidesTest(unittest.TestCase):
    def test_init(self):
        prov = vapi.Provides(5)

        self.assertEqual(prov.since, 5)


class RequiredPropertyTest(unittest.TestCase):
    def test_init(self):
        def test():
            pass

        prop = vapi.RequiredProperty('req', test)

        self.assertTrue(isinstance(prop, property))
        self.assertEqual(prop.__isrequiredmethod__, 'req')


class ProvidesPropertyTest(unittest.TestCase):
    def test_init(self):
        def test():
            pass

        prop = vapi.ProvidesProperty('prov', test)

        self.assertTrue(isinstance(prop, property))
        self.assertEqual(prop.__isprovidedmethod__, 'prov')


class HelperTest(unittest.TestCase):
    def test_no_args(self):
        decorator = mock.Mock()
        cls = mock.Mock()

        result = vapi._helper((), {}, decorator, set(), cls)

        self.assertTrue(isinstance(result, functools.partial))
        self.assertEqual(result.func, decorator)
        self.assertEqual(result.args, (cls.return_value,))
        cls.assert_called_once_with()
        self.assertFalse(decorator.called)

    def test_with_since(self):
        decorator = mock.Mock()
        cls = mock.Mock()

        result = vapi._helper((), {'since': 5}, decorator,
                              set(['since', 'cap']), cls)

        self.assertTrue(isinstance(result, functools.partial))
        self.assertEqual(result.func, decorator)
        self.assertEqual(result.args, (cls.return_value,))
        cls.assert_called_once_with(since=5, caps=None)
        self.assertFalse(decorator.called)

    def test_with_cap_str(self):
        decorator = mock.Mock()
        cls = mock.Mock()

        result = vapi._helper((), {'cap': 'string'}, decorator,
                              set(['since', 'cap']), cls)

        self.assertTrue(isinstance(result, functools.partial))
        self.assertEqual(result.func, decorator)
        self.assertEqual(result.args, (cls.return_value,))
        cls.assert_called_once_with(since=0, caps=frozenset(['string']))
        self.assertFalse(decorator.called)

    def test_with_cap_seq(self):
        decorator = mock.Mock()
        cls = mock.Mock()

        result = vapi._helper((), {'cap': ['a', 'b', 'c']}, decorator,
                              set(['since', 'cap']), cls)

        self.assertTrue(isinstance(result, functools.partial))
        self.assertEqual(result.func, decorator)
        self.assertEqual(result.args, (cls.return_value,))
        cls.assert_called_once_with(since=0, caps=frozenset(['a', 'b', 'c']))
        self.assertFalse(decorator.called)

    def test_with_extra_kwargs(self):
        decorator = mock.Mock()
        cls = mock.Mock()

        self.assertRaises(TypeError, vapi._helper, (), {'cap': 'string'},
                          decorator, set(['since']), cls)
        self.assertFalse(cls.called)
        self.assertFalse(decorator.called)

    def test_with_pos_args(self):
        decorator = mock.Mock()
        cls = mock.Mock()

        result = vapi._helper(('func',), {}, decorator,
                              set(['since', 'cap']), cls)

        self.assertEqual(result, decorator.return_value)
        cls.assert_called_once_with(since=0, caps=None)
        decorator.assert_called_once_with(cls.return_value, 'func')

    def test_with_extra_pos_args(self):
        decorator = mock.Mock()
        cls = mock.Mock()

        self.assertRaises(TypeError, vapi._helper, ('func', 'extra'), {},
                          decorator, set(['since', 'cap']), cls)
        self.assertFalse(cls.called)
        self.assertFalse(decorator.called)


class RequiredDecoratorTest(unittest.TestCase):
    @mock.patch.object(vapi, '_helper')
    def test_basic(self, mock_helper):
        result = vapi.required('func', since=5, cap='spam')

        self.assertEqual(result, mock_helper.return_value)
        mock_helper.assert_called_once_with(
            ('func',), {'since': 5, 'cap': 'spam'}, mock.ANY,
            set(['since', 'cap']), vapi.Required)

        func = mock.Mock()
        decorator = mock_helper.call_args[0][2]

        decorated = decorator('req', func)

        self.assertEqual(decorated, func)
        self.assertEqual(func.__isrequiredmethod__, 'req')


class RequiredPropertyDecoratorTest(unittest.TestCase):
    @mock.patch.object(vapi, '_helper')
    def test_basic(self, mock_helper):
        result = vapi.required_property('func', since=5, cap='spam')

        self.assertEqual(result, mock_helper.return_value)
        mock_helper.assert_called_once_with(
            ('func',), {'since': 5, 'cap': 'spam'}, vapi.RequiredProperty,
            set(['since', 'cap']), vapi.Required)


class ProvidesDecoratorTest(unittest.TestCase):
    @mock.patch.object(vapi, '_helper')
    def test_basic(self, mock_helper):
        result = vapi.provides('func', since=5)

        self.assertEqual(result, mock_helper.return_value)
        mock_helper.assert_called_once_with(
            ('func',), {'since': 5}, mock.ANY, set(['since']), vapi.Provides)

        func = mock.Mock()
        decorator = mock_helper.call_args[0][2]

        decorated = decorator('prov', func)

        self.assertEqual(decorated, func)
        self.assertEqual(func.__isprovidedmethod__, 'prov')


class ProvidesPropertyDecoratorTest(unittest.TestCase):
    @mock.patch.object(vapi, '_helper')
    def test_basic(self, mock_helper):
        result = vapi.provides_property('func', since=5)

        self.assertEqual(result, mock_helper.return_value)
        mock_helper.assert_called_once_with(
            ('func',), {'since': 5}, vapi.ProvidesProperty, set(['since']),
            vapi.Provides)
