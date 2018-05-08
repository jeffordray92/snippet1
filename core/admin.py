from __future__ import absolute_import

from django.conf.urls import url
from django.contrib import admin

from core.models import (
    Business,
    Amenity,
    Sector_DTI_Files,
    Sector_DTI_NCCP,
    Status,
    Location,
)
from core.views import (
    classify_business_to_sectors,
    upload_xls,
    export_excel,
    export_pdf,
    display_analytics,
)

class AmenityInline(admin.TabularInline):
    model = Amenity
    extra = 1


# class DivisionInline(admin.TabularInline):
#     model = Division
#     extra = 1


class CapitalizationFilter(admin.SimpleListFilter):
    title = 'Capitalization'
    parameter_name = 'capital'

    def lookups(self, request, model_admin):
        entries = [
            ('micro', "Micro"),
            ('small', "Small"),
            ('medium', "Medium"),
            ('large', "Large"),
        ]
        return entries

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == 'micro':
                return queryset.filter(capital__lt=3000000)
            elif self.value() == 'small':
                return queryset.filter(capital__gte=3000000,capital__lte=15000000)
            elif self.value() == 'medium':
                return queryset.filter(capital__gt=15000000,capital__lte=100000000)
            elif self.value() == 'large':
                return queryset.filter(capital__gt=100000000)
            else:
                return queryset
        else:
            return queryset


class BusinessAdmin(admin.ModelAdmin):
    # Disabled fields for list display: 'section', 'division',
    # Disabled fields for list filter: 'division__section', 'division',
    list_display = ['taxpayer_name', 'business_name', 'tel_number', 'address', 'barangay', 'business_type', 'ownership_type',
                    'capital', 'year','status', 'sector_dti_files', 'sector_dti_nccp', 'is_verified', ]
    inlines = [AmenityInline,]
    search_fields = ['taxpayer_name', 'business_name', 'address', 'barangay',
                     'capital', 'status__name', 'sector_dti_files__name', 'sector_dti_nccp__name',]
    list_filter = ['business_type', 'ownership_type', CapitalizationFilter, 'year', 'status', 'sector_dti_files', 'sector_dti_nccp',
                   'barangay', 'is_verified',]
    ordering = ('taxpayer_name',)
    exclude = ('division',)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser or request.user.groups.all()[0].name == 'Staff':
            return self.readonly_fields
        #get all fields as readonly
        fields = [f.name for f in self.model._meta.fields]
        return fields

    def get_urls(self):
        urls = super(BusinessAdmin, self).get_urls()
        urlpatterns = [
            url(r'^upload/$', upload_xls, name="upload_excel"),
            url(r'^analytics/$', display_analytics, name="display_analytics"),
            url(r'^analytics/(?P<year>.*)/$', display_analytics, name="display_analytics"),
            url(r'^export_excel/(?P<filters>.*)/$', export_excel, name="export_excel"),
            url(r'^export_pdf/(?P<filters>.*)/$', export_pdf, name="export_pdf"),
            url(r'^classify_to_sectors/(?P<filters>.*)/$', classify_business_to_sectors, name="classify_business_to_sectors"),
        ]
        return urlpatterns + urls

    def section(self, obj):
        try:
            return obj.division.section
        except AttributeError:
            return None
    section.short_description = 'Section'

# =============================================================================
# Disabled admin sections: Section, Division
# =============================================================================
# class SectionAdmin(admin.ModelAdmin):
#     list_display = ['name', 'description', 'code',]
#     inlines = [DivisionInline,]
#     search_fields = ['name', 'code',]
#     ordering = ('code',)


# class DivisionAdmin(admin.ModelAdmin):
#     list_display = ['name', 'description', 'section', 'code',]
#     search_fields = ['name', 'section__name', 'code',]
#     ordering = ('code',)
#     list_filter = ['section']


class Sector_DTI_FilesAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'code',]
    ordering = ('code',)
    search_fields = ['name', 'code',]


class Sector_DTI_NCCPAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'code',]
    ordering = ('code',)
    search_fields = ['name', 'code',]


class StatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    ordering = ('name',)
    search_fields = ['name',]


class LocationAdmin(admin.ModelAdmin):
    list_display = ['establishment',]
    search_fields = ['establishment',]

# =============================================================================
# Disabled admin sections: Section, Division
# =============================================================================
admin.site.register(Business, BusinessAdmin)
admin.site.register(Sector_DTI_Files, Sector_DTI_FilesAdmin)
admin.site.register(Sector_DTI_NCCP, Sector_DTI_NCCPAdmin)
admin.site.register(Status, StatusAdmin)
admin.site.register(Location, LocationAdmin)
# admin.site.register(Section, SectionAdmin)
# admin.site.register(Division, DivisionAdmin)
