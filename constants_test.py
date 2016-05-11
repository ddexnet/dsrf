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

"""Tests for constants."""

import re
import unittest

from dsrf import constants


class BasePatternTest(unittest.TestCase):
  valid_values = []
  invalid_values = []
  pattern = None

  def test_valid_values(self):
    for valid_value in self.valid_values:
      self.assertIsNotNone(self.pattern.match(valid_value))

  def test_invalid_values(self):
    for invalid_value in self.invalid_values:
      self.assertIsNone(self.pattern.match(invalid_value))


class MessageNotificationPeriodPatternTest(BasePatternTest):
  valid_values = ['2015', '2015-02', '2015-200', '2015-02-01--2014-03-05',
                  '2015-12-12', '2015-Q2']
  invalid_values = ['2015-02--2015-03']
  pattern = constants.MESSAGE_NOTIFICATION_PERIOD_PATTERN


class TerritoryOfUseOrSalePatternTest(BasePatternTest):
  valid_values = ['AU', 'Worldwide', '2136', '4', '28', '152']
  invalid_values = ['AAA', 'AAAAA', '12345']
  pattern = constants.TERRITORY_OF_USE_OR_SALE_PATTERN


class MessageCreatedDateTimePatternTest(BasePatternTest):
  valid_values = ['20150723T092522']
  invalid_values = ['20150723T0925220', '20150723092522']
  pattern = constants.MESSAGE_CREATED_DATETIME_PATTERN


class DurationPatternTest(BasePatternTest):
  valid_values = ['P', 'P12', 'P1223', 'P122345', 'P12T12', 'PT12', 'P1223T23',
                  'PT123645', 'P02Y01M01DT12H22M34S', 'PT11H44M22S', 'PT22S',
                  'PT12M23S', 'P23YT12S']
  invalid_values = ['', '12T12']
  pattern = constants.DURATION_PATTERN


class DatatimePatternTest(BasePatternTest):
  valid_values = ['2014-12-14T10:05:00Z', '2014-12-14T10:05:00+08:00']
  invalid_values = ['', '20141214T10:05:00Z', '2014-12-14T100500Z',
                    '2014-12-14T10:05:00', '2014-12-14T10:05:0008:00',
                    '1-12-14T10:05:00Z', '2014-2-14T10:05:00Z',
                    '2014-12-4T10:05:00Z', '2014-12-14T1:05:00Z',
                    '2014-12-14T10:0:00Z', '2014-12-14T10:05:0Z']
  pattern = constants.DATETIME_PATTERN


class GeneralConstantsTest(unittest.TestCase):

  def test_file_name_components(self):
    self.assertEquals(
        len(constants.FILE_NAME_COMPONENTS),
        len(re.split(r'_|of|\.', constants.FILE_NAME_FORMAT))
    )


if __name__ == '__main__':
  unittest.main()
