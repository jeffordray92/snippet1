from __future__ import unicode_literals

import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _

optional = {
    "null": True,
    "blank": True,
}


class Business(models.Model):
    BUSINESS_SINGLE = 1
    BUSINESS_PARTNERSHIP = 2
    BUSINESS_CORPORATION = 3
    BUSINESS_COOPERATIVE = 4
    BUSINESS_WORKERS_ASSOCATION_LABOR_UNION = 5
    BUSINESS_TYPE_CHOICES = (
        (BUSINESS_SINGLE, 'Single'),
        (BUSINESS_PARTNERSHIP, 'Partnership'),
        (BUSINESS_CORPORATION, 'Corporation'),
        (BUSINESS_COOPERATIVE, 'Cooperative'),
        (BUSINESS_WORKERS_ASSOCATION_LABOR_UNION, 'Workers Association/Labor Union'),
    )

    OWNERSHIP_FILIPINO = 1
    OWNERSHIP_PHILIPPINE_FOREIGN_JOINT_VENTURE = 2
    OWNERSHIP_FOREIGN = 3
    OWNERSHIP_TYPE_CHOICES = (
        (OWNERSHIP_FILIPINO, 'Filipino'),
        (OWNERSHIP_PHILIPPINE_FOREIGN_JOINT_VENTURE, 'Philippine-Foreign Joint Venture'),
        (OWNERSHIP_FOREIGN, 'Foreign'),
    )

    taxpayer_name = models.CharField(_("Taxpayer's Name"), max_length=255)
    business_name = models.CharField( _("Business Name"), max_length=255, **optional)
    business_type = models.IntegerField(_("Type of Business"), choices=BUSINESS_TYPE_CHOICES, **optional)
    ownership_type = models.IntegerField(_("Type of Business Ownership"), choices=OWNERSHIP_TYPE_CHOICES, **optional)
    address = models.TextField(_("Business Address"), **optional)
    tel_number = models.CharField(_("Telephone Number"), max_length=100, **optional)
    barangay = models.CharField(_("Barangay"), max_length=255, **optional)
    capital = models.DecimalField(_("Asset Size"), max_digits=20, decimal_places=2, **optional)
    status = models.ForeignKey("Status", **optional)
    sector_dti_files = models.ForeignKey("Sector_DTI_Files", verbose_name="Sector from DTI Files", **optional)
    sector_dti_nccp = models.ForeignKey("Sector_DTI_NCCP", verbose_name="Sector from DTI-NCCP", **optional)
    division = models.ForeignKey("Division", **optional)
    year = models.IntegerField(_("Year Issued"), default=datetime.datetime.now().year)
    is_verified = models.BooleanField(default=False, verbose_name="Is Verified")

    class Meta(object):
        verbose_name = _('Business')
        verbose_name_plural = _('Businesses')

    def __unicode__(self):
        return "{} ({})".format(self.taxpayer_name, self.business_name)


class Amenity(models.Model):
    name = models.CharField(_("Name"), max_length=255)
    establishment = models.ForeignKey('Business')

    class Meta(object):
        verbose_name = _('Line of Business')
        verbose_name_plural = _('Line of Business')

    def __unicode__(self):
        return self.name


class Sector_DTI_Files(models.Model):
    name = models.CharField(_("Name"), max_length=255)
    description = models.TextField(_("Description"), **optional)
    code = models.CharField(_('Code'), max_length=10)

    class Meta(object):
        verbose_name = _('Sector From DTI Files')
        verbose_name_plural = _('Sectors From DTI Files')

    def __unicode__(self):
        return self.name


class Sector_DTI_NCCP(models.Model):
    name = models.CharField(_("Name"), max_length=255)
    description = models.TextField(_("Description"), **optional)
    code = models.CharField(_('Code'), max_length=10)

    class Meta(object):
        verbose_name = _('Sector From DTI-NCCP')
        verbose_name_plural = _('Sectors From DTI-NCCP')

    def __unicode__(self):
        return self.name


class Status(models.Model):
    name = models.CharField(_("Name"), max_length=255)
    description = models.TextField(_("Description"), **optional)

    class Meta(object):
        verbose_name = _('Status')
        verbose_name_plural = _('Statuses')

    def __unicode__(self):
        return self.name


class Location(models.Model):
    establishment = models.ForeignKey("Business")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, **optional)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, **optional)

    class Meta(object):
        verbose_name = _('Location')
        verbose_name_plural = _('Locations')

    def __unicode__(self):
        return "Loc - {}".format(self.establishment)


class Sector_DTI_NCCP_Dataset(models.Model):
    sector_dti_nccp = models.ForeignKey("Sector_DTI_NCCP")
    text = models.TextField(_("Text"))

    class Meta(object):
        verbose_name = _('DTI-NCCP Sectors Dataset')
        verbose_name_plural = _('DTI-NCCP Sectors Datasets')

    def __unicode__(self):
        return unicode(self.id)


class Section(models.Model):
    name = models.CharField(_("Name"), max_length=255)
    description = models.TextField(_("Description"), **optional)
    code = models.CharField(_('Code'), max_length=1)

    class Meta(object):
        verbose_name = _('Section')
        verbose_name_plural = _('Sections')

    def __unicode__(self):
        return self.code


class Division(models.Model):
    name = models.CharField(_("Name"), max_length=255)
    description = models.TextField(_("Description"), **optional)
    section = models.ForeignKey('Section', **optional)
    code = models.CharField(_('Code'), max_length=2)

    class Meta(object):
        verbose_name = _('Division')
        verbose_name_plural = _('Divisions')

    def __unicode__(self):
        return self.code


class PSIC_Group(models.Model):
    name = models.CharField(_("Name"), max_length=255)
    code = models.CharField(_('Code'), max_length=10)
    description = models.TextField(_("Description"), **optional)
    psic_division = models.ForeignKey('Division', **optional)

    class Meta(object):
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')

    def __unicode__(self):
        return self.code


class PSIC_Class(models.Model):
    name = models.CharField(_("Name"), max_length=255)
    code = models.CharField(_('Code'), max_length=10)
    description = models.TextField(_("Description"), **optional)
    psic_group = models.ForeignKey('PSIC_Group', **optional)

    class Meta(object):
        verbose_name = _('Class')
        verbose_name_plural = _('Classes')

    def __unicode__(self):
        return self.code


class PSIC_Subclass(models.Model):
    name = models.CharField(_("Name"), max_length=255)
    code = models.CharField(_('Code'), max_length=10)
    psic_class = models.ForeignKey('PSIC_Class', **optional)

    class Meta(object):
        verbose_name = _('Subclass')
        verbose_name_plural = _('Subclasses')

    def __unicode__(self):
        return self.code
