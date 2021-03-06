# -*- coding: utf-8 -*-
from collective.glossary.interfaces import IGlossary
from collective.glossary.interfaces import IGlossarySettings
from collective.glossary.interfaces import ITerm
from plone import api
from plone.memoize import ram
from Products.Five.browser import BrowserView

import json


def _catalog_counter_cachekey(method, self):
    """Return a cachekey based on catalog updates."""

    catalog = api.portal.get_tool('portal_catalog')
    return str(catalog.getCounter())


class TermView(BrowserView):

    """Default view for Term type"""

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get_entry(self):
        """Get term in the desired format"""

        scales = self.context.unrestrictedTraverse('@@images')
        image = scales.scale('image', None)
        item = {
            'title': self.context.title,
            'description': self.context.description,
            'image': image
        }
        return item


class GlossaryView(BrowserView):

    """Default view of Glossary type"""

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @ram.cache(_catalog_counter_cachekey)
    def get_entries(self):
        """Get glossary entries and keep them in the desired format"""

        catalog = api.portal.get_tool('portal_catalog')
        path = '/'.join(self.context.getPhysicalPath())
        query = dict(portal_type='Term', path={'query': path, 'depth': 1})

        items = {}
        for brain in catalog(**query):
            obj = brain.getObject()
            index = obj.title[0].upper()
            if index not in items:
                items[index] = []
            scales = obj.unrestrictedTraverse('@@images')
            image = scales.scale('image', None)
            item = {
                'title': obj.title,
                'description': obj.description,
                'image': image
            }
            items[index].append(item)

        keys = items.keys()
        for k in keys:
            items[k] = sorted(
                items[k],
                key=lambda term: term['title']
            )

        return items

    def letters(self):
        """Return all letters sorted"""
        return sorted(self.get_entries().keys())

    def terms(self, letter):
        """Return all terms of one letter"""
        return self.get_entries()[letter]


class GlossaryStateView(BrowserView):
    """Glossary State view used to enable or disable resources

    This is called by JS and CSS resources registry
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def tooltip_is_enabled(self):
        """Check if term tooltip is enabled."""
        return api.portal.get_registry_record(
            IGlossarySettings.__identifier__ + '.enable_tooltip'
        )

    def is_view_action(self):
        """Check if we are into the view action"""

        context = self.context
        context_url = context.absolute_url()
        request_url = self.request.base + self.request.get('PATH_INFO', '')
        if context_url == request_url:
            return True

        # Default view
        return context_url.startswith(request_url) and \
            len(context_url) > len(request_url)

    def is_glossary_object(self):
        """Check if we are in the context of a Glossary or a Term."""

        context = self.context
        return IGlossary.providedBy(context) or ITerm.providedBy(context)

    def __call__(self):
        return self.tooltip_is_enabled() and \
            self.is_view_action() and not self.is_glossary_object()


class JsonView(BrowserView):
    """Json view that return all glossary items in json format

    This view is used into an ajax call for
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @ram.cache(_catalog_counter_cachekey)
    def get_json_entries(self):
        """Get all itens and prepare in the desired format.
        Note: do not name it get_entries, otherwise caching is broken. """

        catalog = api.portal.get_tool('portal_catalog')

        items = []
        for brain in catalog(portal_type='Term'):
            items.append({
                'term': brain.Title,
                'description': brain.Description,
            })

        return items

    def __call__(self):
        response = self.request.response
        response.setHeader('content-type', 'application/json')

        return response.setBody(json.dumps(self.get_json_entries()))
