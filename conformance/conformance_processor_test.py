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

"""Tests for dsrf.conformance.conformance_processor."""

import os
from os import path
import sys
import unittest

from google.protobuf import text_format

from dsrf import constants
from dsrf.conformance import conformance_processor
from dsrf.conformance import conformance_validators
from dsrf.conformance import error
from dsrf.parsers import dsrf_report_manager
from dsrf.proto import block_pb2


def read_test_block(file_name):
  return open(
      path.join(
          path.dirname(__file__), '../testdata/blocks/' + file_name)).read()


def _create_test_block(row_types):
  block_proto = block_pb2.Block(type=block_pb2.BODY, number=0, file_number=1)
  row_number = 0
  for row_type in row_types:
    row_number += 1
    row = block_proto.rows.add()
    row.type = row_type
    row.row_number = row_number
  return block_proto


def _write_block_to_queue(row_types):
  open('/tmp/queue.txt', 'w')  # Ensures file gets overwritten.
  ugc_block = _create_test_block(row_types)
  queue_fd = os.open('/tmp/queue.txt', os.O_RDWR)
  os.write(queue_fd, ugc_block.SerializeToString())
  os.write(queue_fd, bytes('\n' + constants.QUEUE_DELIMITER + '\n'))
  sys.stdin = open('/tmp/queue.txt', 'rb')


BODY_BLOCK = read_test_block('basic_body_block.txt')

UGC_XSD_1_1 = path.join(
    path.dirname(__file__),
    '../schemas/UgcProfile/1.1.1/UgcProfile.xsd')


class ConformanceProcessorBasicTest(unittest.TestCase):

  @classmethod
  def block_from_ascii(cls, text):
    """Returns Block protobuf parsed from ASCII text."""
    block = block_pb2.Block()
    text_format.Merge(text, block)
    return block

  def _parse_file(self, filename):
    report_manager = dsrf_report_manager.DSRFReportManager('/tmp/example.log')
    open('/tmp/queue.txt', 'w')  # Overwrites the file if the file exists.
    sys.stdout = open('/tmp/queue.txt', 'r+')
    avs_xsd_file = path.join(
        path.dirname(__file__), '../schemas/avs/current/avs.xsd')
    files_list = [path.join(path.dirname(__file__), filename)]
    sys.stdin = open('/tmp/queue.txt', 'rb')
    report_manager.parse_report(
        files_list, UGC_XSD_1_1, avs_xsd_file, human_readable=False)

  def test_process_block(self):
    r"""Constructs a node tree.

    In addition, reads an ASCII block, serializes and writes it to "stdout" so
    the conformance processor can read it.

    Nodes structure:

       profile root
            |
          choice
          /    \
      sequence  MW01
        / \
    RE01  AS02
    """
    re01 = conformance_validators.Node()
    re01.set_row_type('RE01')
    as02 = conformance_validators.Node()
    as02.set_row_type('AS02')
    sequence = conformance_validators.Node(is_sequence=True)
    sequence.add_child(re01)
    sequence.add_child(as02)
    mw01 = conformance_validators.Node()
    mw01.set_row_type('MW01')
    choice = conformance_validators.Node(max_occurs=float('inf'),
                                         is_choice=True)
    choice.add_child(sequence)
    choice.add_child(mw01)
    root = conformance_validators.Node()
    root.add_child(choice)
    conformance_block_processor = (
        conformance_processor.ConformanceBlockProcessor())
    conformance_block_processor.node = root
    # Verify that two rows were validated successfully.
    nr_rows_validated = conformance_block_processor.process_block(
        self.block_from_ascii(BODY_BLOCK))
    self.assertEqual(nr_rows_validated, 2)

  def test_process_report_valid(self):
    """Verifies the conformance validation for a single valid UGC block."""
    valid_rows = [
        ['AS01', 'MW01', 'RU01', 'SU03', 'LI01', 'LI01', 'LI01'],
        ['AS01', 'MW01', 'RU01', 'SU03', 'LI01', 'LI01'],
        ['AS01', 'MW01', 'RU02', 'SU03', 'LI01', 'LI01', 'LI01'],
        ['AS02'] * 15 + ['RU02'] * 2 + ['SU03'] * 6,
        ['AS01', 'MW01', 'RU01', 'SU03'],
        ['AS01', 'MW01', 'SU03', 'LI01', 'LI01', 'LI01'],
    ]

    for valid_row in valid_rows:
      # Step 1: Write the UGC Block to the "queue".
      _write_block_to_queue(valid_row)

      # Step 2: Read block from queue and perform validation.
      dsrf_xsd_file = path.join(
          path.dirname(__file__), '../testdata/profile_for_conformance.xsd')
      report_processor = conformance_processor.ConformanceReportProcessor(
          dsrf_xsd_file)
      # Need to set this manually since we're not passing a HEAD block.
      report_processor.profile_name = 'UgcProfile'

      nr_blocks_validated, nr_rows_validated = report_processor.process_report()

      self.assertEqual(nr_blocks_validated, 1)
      self.assertEqual(nr_rows_validated, len(valid_row))

  def test_process_report_invalid(self):
    """Verifies the conformance validation for a single valid UGC block."""
    invalid_rows = [
        ['XX01', 'YY01'],
        # MW01 must be preceded by 'AS01'
        ['MW01', 'RU01', 'SU03'],
        ['AS02', 'MW01', 'MW01', 'RU01', 'SU03'],
    ]

    for invalid_row in invalid_rows:
      _write_block_to_queue(invalid_row)

      # Step 2: Read block from queue and perform validation.
      dsrf_xsd_file = path.join(
          path.dirname(__file__), '../testdata/profile_for_conformance.xsd')
      report_processor = conformance_processor.ConformanceReportProcessor(
          dsrf_xsd_file)
      # Need to set this manually since we're not passing a HEAD block.
      report_processor.profile_name = 'UgcProfile'

      expected_error = (
          'Expected structure:\nSequence (Sequence (Sequence ([Sequence (AS01 '
          'and MW01*) or AS02]+))+ and [RU01 or RU02]* and Sequence (SU03 and '
          'LI01*)*)\nActual structure:')
      try:
        report_processor.process_report()
        raise Exception('Row should be invalid but was not: %r' % invalid_row)
      except error.BlockConformanceFailure as e:
        self.assertIn(expected_error, str(e))

  def test_conformance_end2end(self):
    """Tests the full flow, from tsv parsing to conformance validation."""
    self._parse_file(
        '../testdata/DSR_TEST_YouTube_AdSupport-music_2015-Q4_IS_1of1_'
        '20160121T150926.tsv')
    report_processor = conformance_processor.ConformanceReportProcessor(
        UGC_XSD_1_1)

    sys.stdin = open('/tmp/queue.txt', 'rb')
    nr_blocks_validated, nr_rows_validated = report_processor.process_report()
    self.assertEqual(nr_blocks_validated, 4)
    self.assertEqual(nr_rows_validated, 21)

  def test_conformance_end2end_minoccurs_zero(self):
    """Tests the case where an element in a sequence may be omitted."""
    self._parse_file(
        '../testdata/DSR_TEST2_YouTube_AdSupport-music_2015-Q4_IS_1of1_'
        '20160121T150926.tsv')
    report_processor = conformance_processor.ConformanceReportProcessor(
        UGC_XSD_1_1)
    sys.stdin = open('/tmp/queue.txt', 'rb')
    nr_blocks_validated, nr_rows_validated = report_processor.process_report()
    self.assertEqual(nr_blocks_validated, 4)
    self.assertEqual(nr_rows_validated, 20)


if __name__ == '__main__':
  unittest.main()
