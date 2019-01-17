# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.STORAGE
#
# Copyright 2019 by it's authors.

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from bika.lims import api
from bika.lims import bikaMessageFactory as _
from senaite.storage import logger
from senaite.storage import senaiteMessageFactory as _s
import collections

from senaite.storage.browser import BaseView
from senaite.storage.interfaces import IStorageFacility


class StoreSamplesView(BaseView):
    """Store Samples view
    """
    template = ViewPageTemplateFile("templates/store_samples.pt")

    def __init__(self, context, request):
        super(StoreSamplesView, self).__init__(context, request)
        self.context = context
        self.request = request
        self.back_url = self.context.absolute_url()


    def __call__(self):
        form = self.request.form

        # Form submit toggle
        form_submitted = form.get("submitted", False)
        form_store = form.get("button_store", False)
        form_cancel = form.get("button_cancel", False)

        objs = self.get_objects_from_request()

        # No items selected
        if not objs:
            return self.redirect(message=_("No items selected"),
                                 level="warning")

        # Handle store
        if form_submitted and form_store:
            samples = []
            for sample in form.get("samples", []):
                sample_uid = sample.get("uid")
                container_uid = sample.get("container_uid")
                if not sample_uid or not container_uid:
                    continue

                sample = self.get_object_by_uid(sample_uid)
                container = self.get_object_by_uid(container_uid)
                logger.info("Storing sample {} in {}".format(sample.getId(),
                                                             container.getId()))
                # Store
                if container.add_object(sample):
                    samples.append(sample)

            message = _s("Stored {} samples: {}".format(
                len(samples), ", ".join(map(api.get_title, samples))))
            return self.redirect(message=message)

        # Handle cancel
        if form_submitted and form_cancel:
            return self.redirect(message=_s("Sample storing canceled"))

        return self.template()

    def get_samples_data(self):
        """Returns a list of AR data
        """
        for obj in self.get_objects_from_request():
            obj = api.get_object(obj)
            yield {
                "obj": obj,
                "id": api.get_id(obj),
                "uid": api.get_uid(obj),
                "title": api.get_title(obj),
                "path": api.get_path(obj),
                "url": api.get_url(obj),
                "sample_type": api.get_title(obj.getSampleType())
            }

    def get_storage_containers_data(self):
        portal = api.get_portal()
        folder = portal.senaite_storage
        query = {
            "portal_type": "StorageSamplesContainer",
            "sort_on": "sortable_title",
            "sort_order": "ascending",
            "path": {
                "query": "/".join(folder.getPhysicalPath()),
            }
        }

        def get_breadcrumbs(obj, breadcrumbs=None):
            obj = api.get_object(obj)
            if not breadcrumbs:
                breadcrumbs = api.get_title(obj)
            parent = api.get_parent(obj)
            parent_title = api.get_title(parent)
            breadcrumbs = "{} > {}".format(parent_title, breadcrumbs)
            if IStorageFacility.providedBy(obj):
                return breadcrumbs
            return get_breadcrumbs(parent, breadcrumbs)

        for obj in api.search(query, "portal_catalog"):
            obj = api.get_object(obj)
            if obj.is_full():
                continue
            yield {
                "obj": obj,
                "id": api.get_id(obj),
                "uid": api.get_uid(obj),
                "title": get_breadcrumbs(obj),
                "path": api.get_path(obj),
                "url": api.get_url(obj)
            }