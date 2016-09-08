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


import unittest

from dsrf import dsrf_logger
from dsrf import error
from dsrf.parsers import cell_validators


NON_UTF8_DATA = b'\xC3\xC3'


class BaseValidatorTest(unittest.TestCase):
  valid_values = []
  invalid_values = []
  transformed_val_map = {}

  def setUp(self):
    self.logger = dsrf_logger.DSRFLogger(__name__, '/tmp/example.log', True)

  def get_validator(self):
    return None

  def test_valid_values(self):
    for value in self.valid_values:
      try:
        self.get_validator().validate_value(value, 9, 'dsrf_1of1_file.tsv', '1')
      except Exception as e:  # pylint: disable=broad-except
        self.fail('Value "%s" should be valid for validator %s: %s' %
                  (value, type(self.get_validator()).__name__, e))

  def test_invalid_values(self):
    for invalid_value in self.invalid_values:
      try:
        self.get_validator().validate_value(
            invalid_value, 8, 'dsrf_1of1_file.tsv', '1')
      except Exception as e:  # pylint: disable=broad-except
        if not isinstance(e, error.CellValidationFailure):
          self.fail('Value "%s" not handled gracefully by %s: %s' %
                    (invalid_value, type(self.get_validator()).__name__, e))
      else:
        self.fail('Value "%s" should be invalid for validator: %s' %
                  (invalid_value, type(self.get_validator()).__name__))

  def test_transformed_vals(self):
    for val, expected_transform in self.transformed_val_map.iteritems():
      transformed_val = self.get_validator().validate_value(
          val, 9, 'dsrf_1of1_file.tsv', '1')
      if transformed_val != expected_transform:
        self.fail(
            'Value "%s" transforms to "%s" instead of "%s" (validator: %s) .' %
            (val, transformed_val, expected_transform,
             type(self.get_validator())))


class StringValidatorTest(BaseValidatorTest):
  valid_values = ['YouTube']
  invalid_values = [True, 0, 10.2, list(), set(), '', NON_UTF8_DATA]
  transformed_val_map = {'YouTube': 'YouTube'}

  def get_validator(self):
    return cell_validators.StringValidator('string_cell', self.logger)

  def test_non_utf8(self):
    validator = cell_validators.StringValidator(
        'string_cell', self.logger, required=False, repeated=False)
    self.assertRaisesRegexp(
        error.BadUnicodeError,
        r'Cell "string_cell" contained a non-utf8 string: "\'\\xc3\\xc3\'". '
        r'Error detail: "\'utf8\' codec can\'t decode byte 0xc3 in position 0:'
        r' invalid continuation byte". \[Block: 10, Row: 80, '
        r'file=filename.tsv\].',
        validator.validate_value, NON_UTF8_DATA, 80, 'filename.tsv', 10)


class IntegerValidatorTest(BaseValidatorTest):
  valid_values = ['23', '05', '23.00']
  invalid_values = ['asb', '23a', '23.2']
  transformed_val_map = {'23': 23, '05': 5, '23.00': 23}

  def get_validator(self):
    return cell_validators.IntegerValidator('int_cell', self.logger)


class BooleanValidatorTest(BaseValidatorTest):
  valid_values = ['True', 'False', 'TRUE', 'false', 'FaLsE']
  invalid_values = [True, 0, 10.2, list(), set(), '', 'YouTube']
  transformed_val_map = {'True': True, 'False': False, 'TRUE': True,
                         'false': False, 'FaLsE': False}

  def get_validator(self):
    return cell_validators.BooleanValidator('boolean_cell', self.logger)


class DecimalValidatorTest(BaseValidatorTest):
  valid_values = ['8.0', '7.8', '8']
  invalid_values = [list(), set(), '', 'YouTube', '23a']
  transformed_val_map = {'8.0': 8.0, '7.8': 7.8, '8': 8.0}

  def get_validator(self):
    return cell_validators.DecimalValidator('decimal_cell', self.logger)


class PatternValidatorTest(BaseValidatorTest):
  valid_values = ['PADPIDA0', 'PADPIDAA', 'PADPIDAa']
  invalid_values = ['PADPIDA', 'PADPID', 'YouTube', 'PADPIDA ', True, 0, 10.2,
                    list(), set(), '']
  transformed_val_map = {'PADPIDA0': 'PADPIDA0', 'PADPIDAA': 'PADPIDAA',
                         'PADPIDAa': 'PADPIDAa'}

  def get_validator(self):
    return cell_validators.PatternValidator(
        'PADPIDA[a-zA-Z0-9]+', 'pattern_cell', self.logger)


class DurationValidatorTest(BaseValidatorTest):
  valid_values = ['P', 'P12', 'P1223', 'P122345', 'P12T12', 'PT12', 'P1223T23',
                  'PT123645']
  invalid_values = ['12T12', True, 0, 10.2, list(), set(), '']
  transformed_val_map = {'P12': 'P12', 'P1223': 'P1223', 'PT12': 'PT12',
                         'P122345': 'P122345', 'P12T12': 'P12T12', 'P': 'P',
                         'P1223T23': 'P1223T23', 'PT123645': 'PT123645'}

  def get_validator(self):
    return cell_validators.DurationValidator('duration_cell', self.logger)

  def test_required(self):
    validator = cell_validators.DurationValidator(
        'duration_cell', self.logger, required=True, repeated=False)
    self.assertRaisesRegexp(
        error.RequiredCellMissing,
        r'Cell "duration_cell" is required. Value was expected to be ISO 8601 '
        r'duration\. \[Block: 1, Row: 9, file=some_file\.csv\]\.',
        validator.validate_value, '', 9, 'some_file.csv', '1')


class DatetimeValidatorTest(BaseValidatorTest):
  valid_values = ['2014-12-14T10:05:00Z', '2014-12-14T10:05:00+08:00']
  invalid_values = ['', '20141214T10:05:00Z', '2014-12-14T100500Z',
                    '2014-12-14T10:05:00', '2014-12-14T10:05:0008:00', True, 0,
                    10.2, list(), set()]
  transformed_val_map = {
      '2014-12-14T10:05:00Z': '2014-12-14T10:05:00Z',
      '2014-12-14T10:05:00+08:00': '2014-12-14T10:05:00+08:00'}

  def get_validator(self):
    return cell_validators.DateTimeValidator('datetime_cell', self.logger)


class FixedStringValidatorTest(BaseValidatorTest):
  valid_values = ['HEAD', 'FOOT', 'FHEA', 'FFOO', 'SY01', 'RE01']
  invalid_values = ['RE02', True, 0, 10.2, list(), set(), '']
  transformed_val_map = {'HEAD': 'HEAD', 'FOOT': 'FOOT', 'FHEA': 'FHEA',
                         'FFOO': 'FFOO', 'SY01': 'SY01', 'RE01': 'RE01'}

  def get_validator(self):
    return cell_validators.FixedStringValidator(
        ['HEAD', 'FOOT', 'FHEA', 'FFOO', 'SY01', 'RE01'], 'RecordType',
        self.logger)

  def test_case_preserved(self):
    validator = cell_validators.FixedStringValidator(
        ['MyCamelCaseIsImportant'], 'RecordType', self.logger)
    self.assertRaisesRegexp(
        error.CellValidationFailure,
        r'Value was expected to be one of the following: '
        r'\[\'MyCamelCaseIsImportant\'\].',
        validator.validate_value, 'WrongValue', 9, 'some_file.csv', '1')


if __name__ == '__main__':
  unittest.main()
