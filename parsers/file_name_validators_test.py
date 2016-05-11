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

"""Tests for file_name_validators."""

import unittest
from dsrf import constants
from dsrf import error
from dsrf.parsers import file_name_validators


class FileNameValidatorTest(unittest.TestCase):

  def _get_filename(
      self, prefix='DSR', recipient_party_id='PADPIDA2014999999Z',
      message_id='PADPIDA2014111801Y', service_description='AdSupport',
      message_notification_period='2015-02', territory_of_use_or_sale='AU',
      x='3', y='4', message_created_datetime='20150723T092522', ext='tsv'):
    return '_'.join([
        prefix, recipient_party_id, message_id, service_description,
        message_notification_period, territory_of_use_or_sale, x+'of'+y,
        message_created_datetime+'.'+ext])

  def test_file_name_validator(self):
    validator = file_name_validators.FileNameValidator(
        constants.FILE_NAME_COMPONENTS)
    expected_file_name_dict = {
        'DSR': 'DSR', 'MessageRecipient': 'PADPIDA2014999999Z',
        'MessageSender': 'PADPIDA2014111801Y',
        'ServiceDescription': 'AdSupport',
        'MessageNotificationPeriod': '2015-02', 'TerritoryOfUseOrSale': 'AU',
        'x': '3', 'y': '4', 'MessageCreatedDateTime': '20150723T092522',
        'ext': 'tsv'}
    actual_file_name_dict = validator.validate_value(self._get_filename())
    self.assertEquals(actual_file_name_dict, expected_file_name_dict)

  def test_invalid_format(self):
    validator = file_name_validators.FileNameValidator(
        constants.FILE_NAME_COMPONENTS)
    self.assertRaisesRegexp(
        error.FileNameValidationFailure,
        'File 1.csv has invalid filename', validator.validate_value, '1.csv')

  def test_multi_territory(self):
    validator = file_name_validators.FileNameValidator(
        constants.FILE_NAME_COMPONENTS)
    validator.validate_value(
        'DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_'
        'AdSupport_2015-02_multi_3of4_20150723T092522.tsv')

  def test_file_name_xofy_invalid(self):
    self.assertRaisesRegexp(
        error.FileNameValidationFailure,
        'File %s has invalid filename \\(error = File number is not an integer '
        'or does not exist.\\).' % self._get_filename(x='8'),
        file_name_validators.FileNameValidator.validate_xofy, '8', '4',
        self._get_filename(x='8'))

    self.assertRaisesRegexp(
        error.FileNameValidationFailure,
        'File %s has invalid filename \\(error = File number is not an integer '
        'or does not exist.\\).' % self._get_filename(x='3a'),
        file_name_validators.FileNameValidator.validate_xofy, '3a', '4',
        self._get_filename(x='3a'))

  def test_file_name_xofy_valid(self):
    self.assertEquals(
        file_name_validators.FileNameValidator.validate_xofy(
            '3', '4', self._get_filename()), ('3', '4'))
    self.assertEquals(
        file_name_validators.FileNameValidator.validate_xofy(
            '4', '4', self._get_filename()), ('4', '4'))

  def test_file_name_prefix_invalid(self):
    self.assertRaisesRegexp(
        error.FileNameValidationFailure,
        'File %s has invalid filename \\(error = File name should start with '
        '%s.\\).' % (
            self._get_filename(prefix='DSS'), constants.FILE_NAME_PREFIX),
        file_name_validators.FileNameValidator.validate_prefix, 'DSS',
        self._get_filename(prefix='DSS'))

  def test_file_name_prefix_valid(self):
    self.assertEquals(
        file_name_validators.FileNameValidator.validate_prefix(
            'DSR', self._get_filename()), 'DSR')

  def test_file_name_suffix_invalid(self):
    self.assertRaisesRegexp(
        error.FileNameValidationFailure,
        ('File %s has invalid filename \\(error = Suffix "csv" is not valid, '
         "supported suffixes: \\['tsv', 'tsv.gz'\\].\\)." %
         self._get_filename(ext='csv')),
        file_name_validators.FileNameValidator.validate_suffix, 'csv',
        self._get_filename(ext='csv'))

  def test_file_name_suffix_valid(self):
    self.assertEquals(
        file_name_validators.FileNameValidator.validate_suffix(
            'tsv', self._get_filename()), 'tsv')

  def test_split_file_name_valid(self):
    expected_file_name_dict_uncompressed = {
        'DSR': 'DSR', 'MessageRecipient': 'PADPIDA2014999999Z',
        'MessageSender': 'PADPIDA2014111801Y',
        'ServiceDescription': 'AdSupport',
        'MessageNotificationPeriod': '2015-02', 'TerritoryOfUseOrSale': 'AU',
        'x': '3', 'y': '4', 'MessageCreatedDateTime': '20150723T092522',
        'ext': 'tsv'}

    self.assertEquals(
        file_name_validators.FileNameValidator.split_file_name(
            self._get_filename(), constants.FILE_NAME_COMPONENTS),
        expected_file_name_dict_uncompressed)
    expected_file_name_dict_compressed = {
        'DSR': 'DSR', 'MessageRecipient': 'PADPIDA2014999999Z',
        'MessageSender': 'PADPIDA2014111801Y',
        'ServiceDescription': 'AdSupport',
        'MessageNotificationPeriod': '2015-02', 'TerritoryOfUseOrSale': 'AU',
        'x': '3', 'y': '4', 'MessageCreatedDateTime': '20150723T092522',
        'ext': 'tsv.gz'}
    self.assertEquals(
        file_name_validators.FileNameValidator.split_file_name(
            self._get_filename(ext='tsv.gz'), constants.FILE_NAME_COMPONENTS),
        expected_file_name_dict_compressed)

if __name__ == '__main__':
  unittest.main()
