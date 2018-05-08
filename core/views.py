from __future__ import unicode_literals

from copy import deepcopy
import datetime
import logging
import re
import string

from django.db import transaction
from django.db.models import Q, Count
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

import numpy as np
from sklearn.datasets.base import Bunch
from sklearn.feature_extraction.text import (
    CountVectorizer,
    TfidfTransformer,
)
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline

from easy_pdf.rendering import render_to_pdf_response
from xlsxwriter.workbook import Workbook

from core.forms import UploadExcelFileForm
from core.models import (
    Amenity,
    Business,
    Sector_DTI_Files,
    Sector_DTI_NCCP,
    Status,
    Sector_DTI_NCCP_Dataset,
)

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

logger = logging.getLogger(__name__)

def upload_xls(request):
    if request.method == 'POST':
        form = UploadExcelFileForm(request.POST, request.FILES)
        if form.is_valid():
            filehandle = request.FILES.get('file')
            xls_array = np.array(filehandle.get_array())

            logger.info("Uploading and parsing file \'{}\'.".format(filehandle._name))

            year_issued = None
            start_create = False
            current_establishment = None
            file_sector = None
            file_sector_code = None
            file_status = None

            file_sector_code = get_sector_code_from_file(filehandle._name)[0]
            file_sector = Sector_DTI_Files.objects.filter(code=file_sector_code).first()

            # For fetching the status defined from the filename. Defaults to "New" status
            if 'renewal' in filehandle._name.split('.')[0].lower():
                file_status = Status.objects.get(id=2)
            else:
                file_status = Status.objects.get(id=1)

            with transaction.atomic():
                for row in xls_array:
                    if not start_create:
                        secstat_cell = re.split('[\s()]+', unicode(row[0]).lower())

                        if string.join(secstat_cell[:2], '') == 'listof':
                            year_issued = [int(x) for x in secstat_cell if x.isdigit() and (1000 < int(x)< 9999)]

                            # For fetching the sector defined inside the file
                            if not file_sector:
                                file_sector = get_sector_from_file(secstat_cell, file_sector_code)

                    check_taxpayer = unicode(row[1]).translate(dict.fromkeys(map(ord, string.punctuation))).lower()
                    if check_taxpayer == 'taxpayers name':
                        start_create = True
                        logger.info('Processing the XLS file \'{}\''.format(filehandle._name))
                        continue

                    current_establishment = create_business_and_amenity(
                        row,
                        file_sector,
                        file_status,
                        current_establishment,
                        year_issued
                    )

            return HttpResponseRedirect(reverse('admin:core_business_changelist'))

    else:
        form = UploadExcelFileForm()

    return render(
        request,
        'upload_xls_file.html',
        {'form': form}
    )


def export_excel(request, filters):
    output = StringIO.StringIO()

    book = Workbook(output)
    sheet = book.add_worksheet('LIST OF BUSINESSES')

    bold = book.add_format({'bold': True})
    money = book.add_format({'num_format': '"Php" #,##0.00'})


    sheet.write(0, 0, 'LIST OF BUSINESSES', bold)
    columns = ["Taxpayer's Name", "Business Name", "Telephone Number", "Business Address",
               "Barangay", "Type of Business", "Type of Business Ownership", "Capital",
               "Year Issued", "Status", "Sector From DTI Files", "Sector From DTI-NCCP"
    ]
    for item in xrange(0,len(columns)):
        sheet.write(2, item, columns[item],bold)

    businesses = Business.objects.all()
    businesses = filter_businesses(businesses, filters)

    column_width = compare_column_width([0]*12,columns)
    for index, business in enumerate(businesses):
        business_object = [
            business.taxpayer_name,
            business.business_name,
            business.tel_number,
            business.address,
            business.barangay,
            business.get_business_type_display() if business.business_type else "",
            business.get_ownership_type_display() if business.ownership_type else "",
            business.capital,
            business.year,
            business.status.name if business.status else "",
            business.sector_dti_files.name if business.sector_dti_files else "",
            business.sector_dti_nccp.name if business.sector_dti_nccp else "",
        ]
        for object_index in xrange(len(business_object)):
            if object_index == 7:
                sheet.write(index+3,object_index,business_object[object_index], money)
            else:
                sheet.write(index+3,object_index,business_object[object_index])
        column_width = compare_column_width(column_width, business_object)

    for column in xrange(len(column_width)):
        column_name = ["A:A", "B:B", "C:C", "D:D", "E:E", "F:F", "G:G", "H:H", "I:I", "J:J", "K:K", "L:L"]
        sheet.set_column(column_name[column], column_width[column])
    sheet.protect()
    book.close()

    logger.info("Exporting list to XLS file.")

    # construct response
    filename = "dti-sordas-list-of-businesses-{}".format(datetime.datetime.now().date())
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename={}.xlsx".format(filename)

    return response


def export_pdf(request, filters):
    businesses = Business.objects.all()
    businesses = filter_businesses(businesses, filters)

    business_list = []
    for business in businesses:
        business_object = [
            business.taxpayer_name,
            business.business_name,
            business.tel_number,
            business.address,
            business.barangay,
            business.get_business_type_display() if business.business_type else "",
            business.get_ownership_type_display() if business.ownership_type else "",
            unicode('Php {:,.2f}'.format(business.capital)) if business.capital else "",
            business.year,
            business.status.name if business.status else "",
            business.sector_dti_files.name if business.sector_dti_files else "",
            business.sector_dti_nccp.name if business.sector_dti_nccp else "",
        ]
        business_list.append(business_object)

    logger.info("Exporting list to PDF (read-only) file.")

    return render_to_pdf_response(request, 'pdf/pdf_business_list.html', {'business_list':business_list})


def classify_business_to_sectors(request, filters):
    businesses = Business.objects.filter(is_verified=False)
    businesses = filter_businesses(businesses, filters)

    if not businesses:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    data = []
    target = []
    target_names = []
    sector_nccp = Sector_DTI_NCCP.objects.all()

    for target_count, sector in enumerate(sector_nccp, start=0):
        dataset = Sector_DTI_NCCP_Dataset.objects.filter(sector_dti_nccp=sector).prefetch_related()

        for entry in dataset:
            data.append(entry.text)
            target.append(target_count)
            target_names.append(sector.name)

        amenities = Amenity.objects.filter(establishment__is_verified=True, establishment__sector_dti_nccp=sector)
        amenities_str = " ".join(unicode(amenity) for amenity in amenities)

        data.append(amenities_str)
        target.append(target_count)
        target_names.append(sector.name)

    section_data = Bunch(data=data, target=np.array(target), target_names=target_names)

    classifier = Pipeline([('vect', CountVectorizer()),
                         ('tfidf', TfidfTransformer()),
                         ('clf', SGDClassifier(loss='hinge', penalty='l2',
                                               alpha=1e-3, n_iter=5, random_state=42)),
    ])

    business_details = []
    for business in businesses:
        amenities = Amenity.objects.filter(establishment=business)
        amenities_str = " ".join(unicode(amenity) for amenity in amenities)

        business_details.append("{} {}".format(
            unicode(amenities_str),
            unicode(business.sector_dti_files)
        ))

    section_data_clf = classifier.fit(section_data.data, section_data.target)
    predicted = classifier.predict(business_details)

    with transaction.atomic():
        for business, predicted_sector in zip(businesses, predicted):
            business.sector_dti_nccp = sector_nccp[predicted_sector]
            business.save()

            logger.info('\'{}\' assigned to {}: \'{}\''.format(business.business_name, sector_nccp[predicted_sector].code, sector_nccp[predicted_sector].name))

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def get_sector_code_from_file(file_name):
    if str(file_name).find('completed') != -1:
        return re.findall('(.+?)completed', str(file_name))

    elif str(file_name).find('renewal') != -1:
        return re.findall('(.+?)renewal', str(file_name))


def compare_column_width(current_width, item):
    for column in xrange(len(current_width)):
        if item[column]:
            if not isinstance(item[column], basestring):
                if column is 7:
                    item[column] = 'Php {:,.2f}'.format(item[column])
                item[column] = unicode(item[column])
            if len(item[column]) > current_width[column]:
                current_width[column] = len(item[column])
    return current_width


def filter_businesses(business_list, filters):
    filters = [item.split('=') for item in filters.strip('?').split('&')]
    default_sorting = True

    if len(filters[0][0]):
        logger.info("Filtering the list of businesses according to {}".format(", ".join([x for (x,y) in filters])))
        for item in filters:
            if item[0] == 'q' and item[1]:
                business_filter_fields = ['taxpayer_name', 'business_name', 'tel_number', 'address', 'barangay',
                       'business_type', 'ownership_type', 'capital', 'year', 'status__name', 'sector_dti_files__name',
                       'sector_dti_nccp__name',]
                entry_query = get_search_query(item[1], business_filter_fields)
                business_list = business_list.filter(entry_query)
            if '__exact' in item[0]:
                if '__id__exact' in item[0]:
                    field = {item[0].replace('__id__exact',''):item[1]}
                    business_list = business_list.filter(**field)
                else:
                    field = {item[0].replace('__exact',''):item[1]}
                    business_list = business_list.filter(**field)
            if item[0] == 'year':
                field = {'year': item[1]}
                business_list = business_list.filter(**field)
            if item[0] == 'barangay':
                field = {'barangay': item[1].replace('+', ' ')}
                business_list = business_list.filter(**field)
            if item[0] == 'capital':
                if item[1] == 'micro':
                    business_list = business_list.filter(capital__lt=3000000)
                elif item[1] == 'small':
                    business_list = business_list.filter(capital__gte=3000000,capital__lte=15000000)
                elif item[1] == 'medium':
                    business_list = business_list.filter(capital__gt=15000000,capital__lte=100000000)
                elif item[1] == 'large':
                    business_list = business_list.filter(capital__gt=100000000)
            if item[0] == 'o':
                sort_fields = item[1].split(".")
                business_sort_fields = ['taxpayer_name', 'business_name', 'tel_number', 'address', 'barangay',
                       'business_type', 'ownership_type', 'capital', 'year', 'status', 'sector_dti_files',
                       'sector_dti_nccp', 'is_verified',]
                for index in xrange(len(sort_fields)):
                    if sort_fields[index]:
                        default_sorting = False
                        if int(sort_fields[index]) > 0:
                            sort_fields[index] = business_sort_fields[int(sort_fields[index]) - 1]
                        else:
                            sort_fields[index] = "-{}".format(business_sort_fields[abs(int(sort_fields[index])) - 1])
                business_list = business_list.order_by(*sort_fields)

        logger.info("Finished filtering.")

    if default_sorting:
        business_list = business_list.order_by('taxpayer_name')
        logger.info("No filters were specified.")

    return business_list


def create_business_and_amenity(file_line, file_sector, file_status, current_establishment, year_issued):
    try:
        if file_line[0].isdigit():

            business_capital = unicode(file_line[5]).translate(dict.fromkeys(map(ord, ',')))

            address_number = unicode(file_line[3]).split(' ')
            business_address = deepcopy(address_number)
            business_number = address_number.pop()

            if not business_number.replace('-', '').isdigit():
                business_number = None
                business_address = string.join(business_address)

            else:
                if len(business_number.replace('-', '')) < 7:
                    business_number = None
                    business_address = string.join(business_address)
                else:
                    business_address = string.join(address_number)

            business = Business.objects.create(
                taxpayer_name = file_line[1],
                business_name = file_line[2],
                address = business_address,
                tel_number = business_number,
                barangay = file_line[4],
                capital = business_capital,
                sector_dti_files = file_sector,
                status= file_status
            )

            if year_issued:
                business.year = year_issued[0]
                business.save()

            logger.info('Creating Business \'{}({})\''.format(file_line[1], file_line[2]))

            current_establishment = business

        elif file_line[0] == '*':
            Amenity.objects.create(
                name= file_line[1],
                establishment = current_establishment
            )

            logger.info('Creating Amenity \'{}\' for Business \'{}\''.format(file_line[1], current_establishment.business_name))

        return current_establishment

    except ValueError:
        logger.error('Error while creating the database entry for {}'.format(file_line[1]), exc_info=True)


def get_status_from_file(file_desc):
    from_file_status =  re.findall('\d*\s*\((.+?)\)', str(file_desc))[0]
    number_of_matches = 0
    file_status_words = from_file_status.split()
    file_status = None

    for word in file_status_words:
        file_status = Status.objects.filter(name__icontains=word).first()
        if file_status:
            number_of_matches += 1

    if not float(number_of_matches)/len(file_status_words) > 0.5:
        file_status = None

    if not file_status:
        file_status = Status.objects.create(
            name=from_file_status.title()
        )

    return file_status


def get_sector_from_file(file_desc_array, file_sector_code):
    pointer_start = 2
    if file_desc_array[2] == 'registered':
        pointer_start = 3

    pointer_end = pointer_start
    for word in file_desc_array[pointer_start:]:
        if word == 'in':
            break
        pointer_end += 1

    file_sector_name = unicode.title(string.join(file_desc_array[pointer_start:pointer_end], " "))
    file_sector = Sector_DTI_Files.objects.filter(name=file_sector_name).first()

    if not file_sector:
        file_sector = Sector_DTI_Files.objects.create(
            name = file_sector_name,
            code = file_sector_code
        )

    return file_sector

def normalize_query(query_string,
    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
    normspace=re.compile(r'\s{2,}').sub):

    return [normspace('',(t[0] or t[1]).strip()) for t in findterms(query_string)]


def get_search_query(query_string, search_fields):

    '''
    Returns a query, that is a combination of Q objects.
    That combination aims to search keywords within a model by testing the given search fields.
    '''

    query = None # Query to search for every search term
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query


def fetch_upper_bound_of_median(businesses, total_count):
    sorted_businesses = sorted(businesses, key=lambda business: business['num_businesses'], reverse=True)
    median = int(total_count * 0.5)
    upper_half_sum = 0
    upper_bound_businesses = []

    for business in sorted_businesses:
        upper_half_sum += business['num_businesses']
        if (median - upper_half_sum) <= 0:
            break

        business['percent_from_total'] = ( float(business['num_businesses']) / total_count ) * 100
        upper_bound_businesses.append(business)

    return upper_bound_businesses


def display_analytics(request, **kwargs):

    years = Business.objects.values('year').distinct().order_by('-year')

    if 'year' in kwargs:
        if not kwargs.get('year').isdigit():
            return render(request, 'analytics-error.html', {'years':years})
        year_filter = int(kwargs.get('year'))
    else:
        year_filter = int(years.first().get('year'))

    if not {'year':year_filter} in years:
        return render(request, 'analytics-error.html', {'years':years})

    logger.info("Processing Data Anlaytics for Businesses in the Year {}".format(year_filter))

    sector_dti_files_data = Sector_DTI_Files.objects.filter(business__year=year_filter).annotate(num_businesses=Count('business')).order_by('-num_businesses').exclude(num_businesses=0).values('name','num_businesses')
    sector_dti_nccp_data = Sector_DTI_NCCP.objects.filter(business__year=year_filter).annotate(num_businesses=Count('business')).order_by('-num_businesses').exclude(num_businesses=0).values('name','num_businesses')
    status_data = Status.objects.filter(business__year=year_filter).annotate(num_businesses=Count('business')).order_by('-num_businesses').exclude(num_businesses=0).values('name','num_businesses')

    filtered_businesses = Business.objects.filter(year=year_filter)
    filtered_businness_count = filtered_businesses.count()
    barangay_data = fetch_upper_bound_of_median(filtered_businesses.values('barangay').annotate(num_businesses=Count('barangay')), filtered_businness_count)

    capital_data = [
        {'capital': 'Micro', 'value': Business.objects.filter(year=year_filter, capital__lt=3000000).count()},
        {'capital': 'Small', 'value': Business.objects.filter(year=year_filter, capital__gte=3000000,capital__lte=15000000).count()},
        {'capital': 'Medium', 'value': Business.objects.filter(year=year_filter, capital__gt=15000000,capital__lte=100000000).count()},
        {'capital': 'Large', 'value': Business.objects.filter(year=year_filter, capital__gt=100000000).count()},
    ]
    capital_data = [value for value in capital_data if value['value']>0]

    logger.info("Analytics processing done. Rendering Analytics...")

    return render(
        request,
        'analytics.html',
        {
            'years': years,
            'sector_dti_files_data': sector_dti_files_data,
            'sector_dti_nccp_data': sector_dti_nccp_data,
            'status_data': status_data,
            'barangay_data': barangay_data,
            'barangay_size': ( len(barangay_data) * 60 ),
            'capital_data': capital_data,
            'year_filter': year_filter,
        }
    )
