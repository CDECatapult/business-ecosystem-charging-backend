# -*- coding: utf-8 -*-

# Copyright (c) 2013-2015 CoNWeT Lab., Universidad Politécnica de Madrid

# This file is part of WStore.

# WStore is free software: you can redistribute it and/or modify
# it under the terms of the European Union Public Licence (EUPL)
# as published by the European Commission, either version 1.1
# of the License, or (at your option) any later version.

# WStore is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# European Union Public Licence for more details.

# You should have received a copy of the European Union Public Licence
# along with WStore.
# If not, see <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>.

import urllib2
from urlparse import urljoin
from django.contrib.auth.models import User
from django.db import models
from djangotoolbox.fields import ListField, DictField, EmbeddedModelField

from wstore.models import Marketplace
from wstore.models import Organization, Context


class MarketOffering(models.Model):
    marketplace = models.ForeignKey(Marketplace)
    offering_name = models.CharField(max_length=100)


# An application is an offering composed by some
# backend comopents and some resources
class Offering(models.Model):
    name = models.CharField(max_length=50)
    owner_organization = models.ForeignKey(Organization)
    owner_admin_user = models.ForeignKey(User)
    version = models.CharField(max_length=20)
    state = models.CharField(max_length=50)
    description_url = models.CharField(max_length=200, null=True, blank=True)
    marketplaces = ListField(EmbeddedModelField(MarketOffering))
    resources = ListField()
    rating = models.FloatField(default=0)
    comments = ListField()
    tags = ListField()
    image_url = models.CharField(max_length=100)
    related_images = ListField()
    offering_description = DictField()
    notification_url = models.CharField(max_length=100)
    creation_date = models.DateTimeField()
    publication_date = models.DateTimeField(null=True, blank=True)
    applications = ListField()
    open = models.BooleanField(default=False)

    def is_owner(self, user):
        """
        Check if the user is the owner of the offering
        """
        owns = False
        if user.userprofile.current_organization == self.owner_organization and \
                (self.owner_admin_user == user or user.pk in user.userprofile.current_organization.managers):

            owns = True

        return owns

    def _get_site(self):
        return Context.objects.all()[0].site.domain

    def get_uri(self):
        """
        Return the URI of the Offering to be used in USDL documents
        """
        site = self._get_site()

        offering_id = urllib2.quote(self.owner_organization.name + '/' + self.name + '/' + self.version)
        return urljoin(site, 'api/offering/asset_manager/' + offering_id)

    def get_image_url(self):
        """
        Returns the complete URL of the offering image
        """
        site = self._get_site()

        return urljoin(site, self.image_url)

    def get_acquire_url(self):
        site = self._get_site()

        offering_id = urllib2.quote(self.owner_organization.name + '/' + self.name + '/' + self.version)
        return urljoin(site, 'offering/' + offering_id)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'wstore'
        unique_together = ('name', 'owner_organization', 'version')


# This embedded class is used to save old versions
# of resources to allow downgrades
class ResourceVersion(models.Model):
    version = models.CharField(max_length=20)
    resource_path = models.CharField(max_length=100)
    download_link = models.CharField(max_length=200)


class Resource(models.Model):
    product_ref = models.URLField()
    version = models.CharField(max_length=20)  # This field maps the Product Spec version
    provider = models.ForeignKey(Organization)
    content_type = models.CharField(max_length=50)
    download_link = models.CharField(max_length=200)
    resource_path = models.CharField(max_length=100)
    old_versions = ListField(EmbeddedModelField(ResourceVersion))
    state = models.CharField(max_length=20)
    resource_type = models.CharField(max_length=100)
    meta_info = DictField()

    def get_url(self):
        url = None

        if self.download_link:
            url = self.download_link
        else:
            # Build the URL for downloading the resource from WStore
            cnt = Context.objects.all()[0]
            url = urljoin(cnt.site.domain, self.resource_path)

        return url

    def get_uri(self):
        site_context = Context.objects.all()[0]
        base_uri = site_context.site.domain
        resource_id = urllib2.quote(self.provider.name + '/' + self.name + '/' + self.version)

        return urljoin(base_uri, 'api/offering/resources/' + resource_id)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'wstore'


class ResourcePlugin(models.Model):
    plugin_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    author = models.CharField(max_length=100)
    form = DictField()
    module = models.CharField(max_length=200)
    media_types = ListField(models.CharField(max_length=100))
    formats = ListField(models.CharField(max_length=10))
    overrides = ListField(models.CharField(max_length=10))
    options = DictField()

    def __unicode__(self):
        return self.plugin_id

    class Meta:
        app_label = 'wstore'
