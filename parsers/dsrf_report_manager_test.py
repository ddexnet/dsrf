# -*- coding: utf-8 -*-
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

"""Tests for dsrf_report_manager."""

from os import path
import sys
import unittest

from google.protobuf import text_format

from dsrf import constants
from dsrf import error
from dsrf.parsers import dsrf_report_manager
from dsrf.proto import block_pb2


def read_test_block(file_name):
  return open(
      path.join(path.dirname(__file__), '../testdata/blocks/' + file_name),
      'r').read()

HEAD_BLOCK = read_test_block('basic_head_block.txt')
BODY_BLOCK = read_test_block('basic_body_block.txt')


class DsrfReportManagerTest(unittest.TestCase):

  def setUp(self):
    self.maxDiff = None  # Allow self.assertMultiLineEqual to show all diffs.
    open('/tmp/queue.txt', 'w')  # Overwrites the file if the file exists.
    self.report_manager = dsrf_report_manager.DSRFReportManager(
        '/tmp/example.log')
    sys.stdout = open('/tmp/queue.txt', 'r+')

  @classmethod
  def block_from_ascii(cls, text):
    """Returns Block protobuf parsed from ASCII text."""
    block = block_pb2.Block()
    text_format.Merge(text, block)
    return block

  def test_validate_head_block_valid(self):
    block = self.block_from_ascii(HEAD_BLOCK)
    file_name = ('DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_'
                 'AU_1of1_20150723T092522.tsv')
    file_name_dict = {
        'DSR': 'DSR', 'MessageRecipient': 'PADPIDA2014999999Z',
        'MessageSender': 'PADPIDA2014801Y',
        'ServiceDescription': 'AdSupport',
        'MessageNotificationPeriod': '2015-02', 'TerritoryOfUseOrSale': 'AU',
        'x': '1', 'y': '1', 'MessageCreatedDateTime': '20150723T092522',
        'ext': 'tsv'}
    self.report_manager.validate_head_block(block, file_name, file_name_dict)

  def test_validate_head_block_invalid(self):
    block = self.block_from_ascii(HEAD_BLOCK)
    file_name = ('DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_'
                 'AU_3of4_20150723T092522.tsv')
    file_name_dict = {
        'DSR': 'DSR', 'MessageRecipient': 'PADPIDA2014999999Z',
        'MessageSender': 'PADPIDA2014111801Y',
        'ServiceDescription': 'AdSupport',
        'MessageNotificationPeriod': '2015-02', 'TerritoryOfUseOrSale': 'AU',
        'x': '3', 'y': '4', 'MessageCreatedDateTime': '20150723T092522',
        'ext': 'tsv'}

    self.assertRaisesRegexp(
        error.FileNameValidationFailure,
        'File DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_'
        '3of4_20150723T092522.tsv has invalid filename \\(error = \\[FHEA: '
        'row 3\\]: The cell "FileNumber" with the value "1" does not match the '
        'file name part "x" with the value "3" in file number 3.\\).',
        self.report_manager.validate_head_block, block, file_name,
        file_name_dict)

  def test_validate_head_block_multi_service(self):
    block = self.block_from_ascii(
        read_test_block('head_block_multi_service.txt'))
    file_name = ('DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_Multi_2015-02_'
                 'AU_1of1_20150723T092522.tsv')
    file_name_dict = {
        'DSR': 'DSR', 'MessageRecipient': 'PADPIDA2014999999Z',
        'MessageSender': 'PADPIDA2014111801Y',
        'ServiceDescription': 'Multi',
        'MessageNotificationPeriod': '2015-02', 'TerritoryOfUseOrSale': 'AU',
        'x': '1', 'y': '1', 'MessageCreatedDateTime': '20150723T092522',
        'ext': 'tsv'}

    self.report_manager.validate_head_block(block, file_name, file_name_dict)

  def test_parse_report_valid_human_readable(self):
    dsrf_xsd_file = path.join(
        path.dirname(__file__), '../testdata/sales-reporting-flat.xsd')
    avs_xsd_file = path.join(
        path.dirname(__file__), '../testdata/avs.xsd')
    files_list = [path.join(
        path.dirname(__file__), '../testdata/DSR_PADPIDA2014999999Z_'
        'PADPIDA2014111801Y_AdSupport_2015-02_AU_1of1_20150723T092522.tsv')]
    self.report_manager.parse_report(
        files_list, dsrf_xsd_file, avs_xsd_file,
        human_readable=True, write_head=False)
    self.assertMultiLineEqual(
        BODY_BLOCK + '\n' + constants.QUEUE_DELIMITER + '\n',
        open('/tmp/queue.txt', 'r').read())

  def test_parse_report_valid_not_human_readable(self):
    dsrf_xsd_file = path.join(
        path.dirname(__file__), '../testdata/sales-reporting-flat.xsd')
    avs_xsd_file = path.join(
        path.dirname(__file__), '../testdata/avs.xsd')
    files_list = [path.join(
        path.dirname(__file__), '../testdata/DSR_PADPIDA2014999999Z_'
        'PADPIDA2014111801Y_AdSupport_2015-02_AU_1of1_20150723T092522.tsv')]
    self.report_manager.parse_report(
        files_list, dsrf_xsd_file, avs_xsd_file,
        human_readable=False, write_head=False)
    serialized_block_str = open('/tmp/queue.txt', 'r').read().split(
        '\n' + constants.QUEUE_DELIMITER)[0]
    deserialized_block_str = unicode(
        block_pb2.Block.FromString(serialized_block_str)).encode('utf-8')
    self.assertMultiLineEqual(BODY_BLOCK, deserialized_block_str)

  def test_parse_report_head_mismatch(self):
    """The cell RecipientPartyId mismatch the file name part RecipientMessage.
    """
    xsd_filename = path.join(
        path.dirname(__file__), '../testdata/sales-reporting-flat.xsd')
    avs_filename = path.join(
        path.dirname(__file__), '../testdata/avs.xsd')
    files_list = [path.join(
        path.dirname(__file__), '../testdata/DSR_PADPIDA2014999999Z_'
        'PADPIDA2014111801Y_AdSupport_2015-02_AU_1of1_20140617T092522.tsv')]
    logger = self.report_manager.parse_report(
        files_list, xsd_filename, avs_filename,
        human_readable=True)
    self.assertEqual(
        logger.first_error,
        'File DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_AdSupport_2015-02_AU_'
        '1of1_20140617T092522.tsv has invalid filename (error = [HEAD: row 1]: '
        'The cell "NumberOfFiles" with the value "2" does not match the file '
        'name part "y" with the value "1" in file number 1.).')

  def test_parse_report_repeated_block_number(self):
    dsrf_xsd_file = path.join(
        path.dirname(__file__), '../testdata/sales-reporting-flat.xsd')
    avs_xsd_file = path.join(
        path.dirname(__file__), '../testdata/avs.xsd')
    files_list = [path.join(
        path.dirname(__file__), '../testdata/DSR_PADPIDA2014999999Z_'
        'PADPIDA2014111801Y_AdSupport_2015-02_AU_2of2_20150723T092522.tsv'),
                  path.join(
                      path.dirname(__file__),
                      '../testdata/DSR_PADPIDA2014999999Z_PADPIDA2014111801Y_'
                      'AdSupport_2015-02_AU_1of2_20150723T092522.tsv')]
    self.assertRaisesRegexp(
        error.ReportValidationFailure, 'The block number 1 is not unique. It '
        'appears in files number: 1 and 2.',
        self.report_manager.parse_report, files_list, dsrf_xsd_file,
        avs_xsd_file, human_readable=True)

  def test_party_filename_head_mismatch(self):
    file_name_dict = {'MessageSender': 'Someone'}
    message_sender_cells = {
        'SenderPartyId': 'PADPIDA2014999999Z',
        'SenderName': 'SomeoneElse'}
    self.assertRaisesRegexp(
        error.FileNameValidationFailure,
        r'File filename\.tsv has invalid filename \(error = The MessageSender '
        r'value in the filename \("Someone"\) did not match either of the '
        r'SenderPartyId \("PADPIDA2014999999Z"\) or the SenderName '
        r'\("SomeoneElse"\) in the HEAD row\)\.',
        dsrf_report_manager._validate_party_filename, 'filename.tsv',
        file_name_dict, message_sender_cells, 'Sender')

if __name__ == '__main__':
  unittest.main()
