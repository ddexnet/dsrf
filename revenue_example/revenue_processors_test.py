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

"""Tests for dsrf.revenue_example.revenue_processors."""

from os import path
import sys
import unittest
from google.protobuf import text_format
from dsrf.parsers import dsrf_report_manager
from dsrf.proto import block_pb2
from dsrf.revenue_example import revenue_processors


class RevenueProcessorsTest(unittest.TestCase):

  @classmethod
  def block_from_ascii(cls, text):
    """Returns Block protobuf parsed from ASCII text."""
    block = block_pb2.Block()
    text_format.Merge(text, block)
    return block

  def test_revenue_example_dsrf_3_0(self):
    report_manager = dsrf_report_manager.DSRFReportManager()
    open('/tmp/queue.txt', 'w')  # Overwrites the file if the file exists.
    sys.stdout = open('/tmp/queue.txt', 'r+')
    log_file = '/tmp/example.log'

    dsrf_xsd_file = path.join(
        path.dirname(__file__), '../schemas/3.0/sales-reporting-flat.xsd')
    avs_xsd_file = path.join(
        path.dirname(__file__), '../schemas/3.0/avs.xsd')
    files_list = [path.join(
        path.dirname(__file__),
        '../testdata/DSR_TEST_YouTube_AdSupport-'
        'music_2015-Q4_IS_1of1_20160121T150926.tsv')]
    report_manager.parse_report(
        files_list, dsrf_xsd_file, avs_xsd_file, log_file,
        human_readable=False)
    sys.stdin = open('/tmp/queue.txt', 'rb')
    processor = revenue_processors.CalculateAllocatedAmount('PUB_2')
    amount, currency = processor.process_report()
    self.assertEquals(amount, 125.23)
    self.assertEquals(currency, 'USD')


if __name__ == '__main__':
  unittest.main()
