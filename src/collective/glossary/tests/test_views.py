# -*- coding: utf-8 -*-
from collective.glossary.interfaces import IGlossaryLayer
from collective.glossary.interfaces import IGlossarySettings
from collective.glossary.testing import INTEGRATION_TESTING
from plone import api
from zope.interface import alsoProvides
from zope.publisher.browser import TestRequest

import unittest


class BaseViewTestCase(unittest.TestCase):

    layer = INTEGRATION_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        alsoProvides(self.request, IGlossaryLayer)

        with api.env.adopt_roles(['Manager']):
            self.g1 = api.content.create(
                self.portal, 'Glossary', 'g1',
                title='Glossary',
                description='Glossary Description'
            )
            self.t1 = api.content.create(
                self.g1, 'Term', 't1',
                title='First Term',
                description='First Term Description'
            )
            self.t2 = api.content.create(
                self.g1, 'Term', 't2',
                title='Second Term',
                description='Second Term Description'
            )


class TermViewTestCase(BaseViewTestCase):

    def setUp(self):
        super(TermViewTestCase, self).setUp()
        self.view = api.content.get_view(u'view', self.t1, self.request)

    def test_get_entry(self):
        self.assertEqual(
            self.view.get_entry(),
            {'description': 'First Term Description',
             'image': None,
             'title': 'First Term'}
        )


class GlossaryViewTestCase(BaseViewTestCase):

    def setUp(self):
        super(GlossaryViewTestCase, self).setUp()
        self.view = api.content.get_view(u'view', self.g1, self.request)

    def test_get_entries(self):
        self.assertEqual(
            self.view.get_entries(),
            {
                'F': [{
                    'image': None,
                    'description': 'First Term Description',
                    'title': 'First Term'
                }],
                'S': [{
                    'image': None,
                    'description': 'Second Term Description',
                    'title': 'Second Term'
                }]
            }
        )

    def test_letters(self):
        self.assertEqual(self.view.letters(), [u'F', u'S'])

    def test_terms(self):
        self.assertEqual(
            self.view.terms('F'),
            [{'image': None,
              'description': 'First Term Description',
              'title': 'First Term'}]
        )
        self.assertEqual(
            self.view.terms('S'),
            [{'image': None,
              'description': 'Second Term Description',
              'title': 'Second Term'}]
        )


class GlossaryStateViewTestCase(BaseViewTestCase):

    def setUp(self):
        super(GlossaryStateViewTestCase, self).setUp()
        self.view = api.content.get_view(u'glossary_state', self.portal, self.request)

    def test_tooltip_is_enabled(self):
        api.portal.set_registry_record(
            IGlossarySettings.__identifier__ + '.enable_tooltip',
            True
        )
        self.assertTrue(self.view.tooltip_is_enabled())

        api.portal.set_registry_record(
            IGlossarySettings.__identifier__ + '.enable_tooltip',
            False
        )
        self.assertFalse(self.view.tooltip_is_enabled())

    def test_is_view_action(self):
        self.assertTrue(self.view.is_view_action())

        self.view.request = TestRequest(environ={
            'SERVER_URL': 'http://nohost',
            'PATH_INFO': '/folder_contents'
        })
        self.view.request.base = 'http://nohost/plone'
        self.assertFalse(self.view.is_view_action())

        self.view.context = self.g1
        self.view.request = TestRequest(environ={
            'SERVER_URL': 'http://nohost/plone/g1',
            'PATH_INFO': '/g1'
        })
        self.view.request.base = 'http://nohost/plone'
        self.assertTrue(self.view.is_view_action())

        self.view.request = TestRequest(environ={
            'SERVER_URL': 'http://nohost/plone/g1',
            'PATH_INFO': '/g1/edit'
        })
        self.view.request.base = 'http://nohost/plone'
        self.assertFalse(self.view.is_view_action())

    def test_is_glossary_object(self):
        self.assertFalse(self.view.is_glossary_object())

        self.view.context = self.g1
        self.view.request = TestRequest()
        self.assertTrue(self.view.is_glossary_object())

        self.view.context = self.portal
        self.assertFalse(self.view.is_glossary_object())

        self.view.context = self.t1
        self.assertTrue(self.view.is_glossary_object())


class JsonViewTestCase(BaseViewTestCase):

    def setUp(self):
        super(JsonViewTestCase, self).setUp()
        self.view = api.content.get_view(
            u'glossary',
            self.portal,
            self.request
        )

    def test_get_json_entries(self):
        self.assertEqual(
            self.view.get_json_entries(),
            [{'description': 'First Term Description', 'term': 'First Term'},
             {'description': 'Second Term Description', 'term': 'Second Term'}]
        )

    def test__call__(self):
        import json

        self.view()
        result = self.view.request.response.getBody()
        self.assertEqual(
            json.loads(result),
            [{'description': 'First Term Description', 'term': 'First Term'},
             {'description': 'Second Term Description', 'term': 'Second Term'}]
        )
