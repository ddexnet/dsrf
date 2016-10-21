# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""The constants of the dsrf parsing library."""

import re

COLOR_GREEN = '\033[92m'
COLOR_RED = '\033[01;31m'
ENDC = '\033[0m'
BOLD = '\033[1m'


# The XSD tags prefix.
XSD_TAG_PREFIX = '{http://www.w3.org/2001/XMLSchema}'

# All row type declarations in the XSD have to start with this value.
VALID_ROW_TYPE_PREFIX = 'RecordType-'


def is_row_type(s):
  return s.startswith(VALID_ROW_TYPE_PREFIX)

# In the TSV, versioned row types contain periods, eg. "SY02.01".
VERSIONED_TSV_ROW_TYPE_PATTERN = re.compile(r'^[A-Z]{2}\d{2}\.\d{2}$')

# Block Id cell's pattern.
BLOCK_PATTERN = re.compile('BL[0-9]+')

# The flat file cells delimiter.
FILE_DELIMITER = '\t'

# The flat file secondary cells delimiter.
REPEATED_VALUE_DELIMITER = '|'

# The flat file delimiter escaper.
ESCAPER = '\\'

# A comment line sign.
COMMENT_SIGN = '#'

# Row types which are considered as part of the header, i.e. they occur only at
# the top of the file.
HEADER_ROW_PATTERN = re.compile('^SY[0-9]{2,4}$|HEAD|FHEA')

# Row types which are considered as block type FOOT.
FOOT_ROWS = ['FOOT', 'FFOO']

# Fixed string cells type prefix (AVS = Allowed Value Set).
FIXED_STRING_PREFIX = 'avs:'

# Simple cells type prefix.
DSRF_TYPE_PREFIX = 'dsrf:'

# Gzip compressed file extension.
GZIP_COMPRESSED_FILE_SUFFIX = '.tsv.gz'

# The format file name delimiter.
FILE_NAME_DELIMITER = r'_'

# The file name format.
FILE_NAME_FORMAT = (
    'DSR_MessageRecipient_MessageSender_ServiceDescription_MessageNotification'
    'Period_TerritoryOfUseOrSale_xofy_MessageCreatedDateTime.ext')

# File name prefix.
FILE_NAME_PREFIX = 'DSR'

# File name components list.
FILE_NAME_COMPONENTS = [
    FILE_NAME_PREFIX,
    'MessageRecipient',
    'MessageSender',
    'ServiceDescription',
    'MessageNotificationPeriod',
    'TerritoryOfUseOrSale',
    'x',
    'y',
    'MessageCreatedDateTime',
    'ext']

# Supported file types.
SUPPORTED_FILE_EXTENSIONS = ['tsv', 'tsv.gz']

# A pattern for the component MessageNotificationPeriod.
MESSAGE_NOTIFICATION_PERIOD_PATTERN = re.compile(
    r'^\d{4}((-\d{2,3})|(-\d{2}-\d{2}(--\d{4}-\d{2}-\d{2})?)|(-Q\d{1}))?$')

# A pattern for the component TerritoryOfUseOrSale. This accepts the following:
#  - Empty string
#  - Two-letter ISO code
#  - CISAC TIS code
#  - "Multi"
#  - "Worldwide"
TERRITORY_OF_USE_OR_SALE_PATTERN = re.compile(
    r'^$|^(\w{2}|\d{1,4}|Worldwide|multi)$', re.IGNORECASE)

# A pattern for the component MessageCreated-DateTime.
MESSAGE_CREATED_DATETIME_PATTERN = re.compile(r'^\d{8}T\d{6}$')

# These parts of the filename are not allowed to change across files.
FILE_NAME_MATCH_PARTS = [
    'MessageRecipient', 'MessageSender', 'ServiceDescription', 'y']

# These HEAD row cells (keys) should match the file name parts (values).
HEAD_CELLS_MATCH_TO_FILE_NAME_PARTS = {
    'FileNumber': 'x',
    'NumberOfFiles': 'y',
    'ServiceDescription': 'ServiceDescription'}

# One of these HEAD cells should match the MessageRecipient part in the file
# name.
MESSAGE_RECIPIENT_MATCH = ['RecipientPartyId', 'RecipientName']

# One of these HEAD cells should match the MessageSender part in the file name.
MESSAGE_SENDER_MATCH = ['SenderPartyId', 'SenderName']

# In the default implementation, the serialized proto objects are written as a
# byte stream. This delimiter enables the reader of the stream to reconstruct
# the individual protos.
QUEUE_DELIMITER = '==PIPE_PROTO_DELIMITER=='

# The xs:duration cell pattern.
DURATION_PATTERN = re.compile(
    r'^(?P<sign>[+-])?'
    r'P(?!\b)'
    r'(?P<years>[0-9]+([,.][0-9]+)?Y)?'
    r'(?P<months>[0-9]+([,.][0-9]+)?M)?'
    r'(?P<weeks>[0-9]+([,.][0-9]+)?W)?'
    r'(?P<days>[0-9]+([,.][0-9]+)?D)?'
    r'((?P<separator>T)(?P<hours>[0-9]+([,.][0-9]+)?H)?'
    r'(?P<minutes>[0-9]+([,.][0-9]+)?M)?'
    r'(?P<seconds>[0-9]+([,.][0-9]+)?S)?)?$')

# The xs:dateTime cell pattern.
DATETIME_PATTERN = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:'
                              r'[0-9]{2}(Z|([-+][0-9]{2}:{0,1}[0-9]{2}))')

# The library default version number.
DEFAULT_VERSION = 3.0
