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

"""Tests for report_files_validators."""

import unittest

import six

from dsrf import constants
from dsrf import dsrf_logger
from dsrf import error
from dsrf.parsers import file_name_validators
from dsrf.parsers import report_files_validators


class ReportFilesValidatorsTest(unittest.TestCase):

  def setUp(self):
    self.validator = report_files_validators.ReportFilesValidator(
        file_name_validators.FileNameValidator(constants.FILE_NAME_COMPONENTS),
        dsrf_logger.DSRFLogger(__name__, '/tmp/example.log', True))

  def test_valid_values(self):
    files_list = [
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_1of4_'
        '20150723T092522.tsv.gz',
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_2of4_'
        '20150723T092522.tsv.gz',
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_3of4_'
        '20150723T092522.tsv.gz',
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_4of4_'
        '20150723T092522.tsv.gz']
    actual_file_name_dicts = self.validator.validate_file_names(files_list)
    expected_file_name_dicts = {
        '1': {'DSR': 'DSR', 'MessageRecipient': 'PADPIDA2014999999Z',
              'MessageSender': 'PADPIDA2014111801Y',
              'ServiceDescription': 'AdSupport',
              'MessageNotificationPeriod': '2015-02',
              'TerritoryOfUseOrSale': 'AU', 'x': '1', 'y': '4',
              'MessageCreatedDateTime': '20150723T092522', 'ext': 'tsv.gz'},
        '2': {'DSR': 'DSR', 'MessageRecipient': 'PADPIDA2014999999Z',
              'MessageSender': 'PADPIDA2014111801Y',
              'ServiceDescription': 'AdSupport',
              'MessageNotificationPeriod': '2015-02',
              'TerritoryOfUseOrSale': 'AU', 'x': '2', 'y': '4',
              'MessageCreatedDateTime': '20150723T092522', 'ext': 'tsv.gz'},
        '3': {'DSR': 'DSR', 'MessageRecipient': 'PADPIDA2014999999Z',
              'MessageSender': 'PADPIDA2014111801Y',
              'ServiceDescription': 'AdSupport',
              'MessageNotificationPeriod': '2015-02',
              'TerritoryOfUseOrSale': 'AU', 'x': '3', 'y': '4',
              'MessageCreatedDateTime': '20150723T092522', 'ext': 'tsv.gz'},
        '4': {'DSR': 'DSR', 'MessageRecipient': 'PADPIDA2014999999Z',
              'MessageSender': 'PADPIDA2014111801Y',
              'ServiceDescription': 'AdSupport',
              'MessageNotificationPeriod': '2015-02',
              'TerritoryOfUseOrSale': 'AU', 'x': '4', 'y': '4',
              'MessageCreatedDateTime': '20150723T092522', 'ext': 'tsv.gz'}
    }
    self.assertEqual(actual_file_name_dicts, expected_file_name_dicts)

  def test_missing_file(self):
    files_list = [
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_2of4_'
        '20150723T092522.tsv.gz',
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_3of4_'
        '20150723T092522.tsv.gz',
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_4of4_'
        '20150723T092522.tsv.gz']
    with six.assertRaisesRegex(self, error.ReportValidationFailure,
                               'File number 1 is missing in the report.'):
      self.validator.validate_file_names(files_list)

  def test_mismatch_file(self):
    files_list = [
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_1of4_'
        '20150723T092522.tsv.gz',
        'DSR_PADPIDA2_PADPIDA2014111801Y_AdSupport_2015-02_AU_2of4_'
        '20150723T092522.tsv.gz',
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_3of4_'
        '20150723T092522.tsv.gz',
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_4of4_'
        '20150723T092522.tsv.gz']
    with six.assertRaisesRegex(
        self, error.ReportValidationFailure,
        'File DSR_PADPIDA2_PADPIDA2014111801Y_AdSupport_2015-02_AU_2of4_'
        '20150723T092522.tsv.gz has invalid filename \\(error = The '
        'MessageRecipient value "PADPIDA2" is expected to match the other files'
        ' in the report and be "PADPIDA2014999999Z".\\).'):
      self.validator.validate_file_names(files_list)

  def test_mismatch_file_without_fail_fast(self):
    self.validator = report_files_validators.ReportFilesValidator(
        file_name_validators.FileNameValidator(constants.FILE_NAME_COMPONENTS),
        dsrf_logger.DSRFLogger(__name__, '/tmp/example.log', False))
    files_list = [
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_1of4_'
        '20150723T092522.tsv.gz',
        'DSR_PADPIDA2_PADPIDA2014111801Y_AdSupport_2015-02_AU_2of4_'
        '20150723T092522.tsv.gz',
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_3of4_'
        '20150723T092522.tsv.gz',
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_4of4_'
        '20150723T092522.tsv.gz']
    with six.assertRaisesRegex(
        self, error.ReportValidationFailure,
        'Found 1 fatal error\\(s\\) and 0 warnings, please check log file at '
        '"/tmp/example.log" for details.\nFirst error: File '):
      self.validator.validate_file_names(files_list)

  def test_file_numbers_repetition(self):
    files_list = [
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_2of4_'
        '20150723T092522.tsv.gz',
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_2of4_'
        '20150723T092522.tsv.gz',
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_3of4_'
        '20150723T092522.tsv.gz',
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_4of4_'
        '20150723T092522.tsv.gz']
    with six.assertRaisesRegex(self, error.ReportValidationFailure,
                               'File number 2 is not unique.'):
      self.validator.validate_file_names(files_list)

  def test_empty_list(self):
    files_list = []
    with six.assertRaisesRegex(self, error.ReportValidationFailure,
                               'Please provide a non-empty list of files.'):
      self.validator.validate_file_names(files_list)


if __name__ == '__main__':
  unittest.main()
