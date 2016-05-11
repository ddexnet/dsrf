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


import os
from os import path
import sys
import unittest

from google.protobuf import text_format

from dsrf import constants
from dsrf.processor import dsrf_block_processor
from dsrf.processor import dsrf_report_processor
from dsrf.proto import block_pb2


def read_test_block(file_name):
  return open(
      path.join(path.dirname(__file__), '../testdata/blocks/' + file_name),
      'r').read()

BASIC_HEAD_BLOCK = read_test_block('basic_head_block.txt')
BASIC_BODY_BLOCK = read_test_block('basic_body_block.txt')


class DsrfReportProcessorTest(unittest.TestCase):

  @classmethod
  def block_from_ascii(cls, text):
    """Returns Block protobuf parsed from ASCII text."""
    block = block_pb2.Block()
    text_format.Merge(text, block)
    return block

  def setUp(self):
    self.maxDiff = None  # Allow self.assertMultiLineEqual to show all diffs.
    open('/tmp/queue.txt', 'w')  # Overwrites the file if the file exists.
    head_block = self.block_from_ascii(BASIC_HEAD_BLOCK)
    body_block = self.block_from_ascii(BASIC_BODY_BLOCK)
    queue_fd = os.open('/tmp/queue.txt', os.O_RDWR)
    os.write(queue_fd, head_block.SerializeToString())
    os.write(queue_fd, bytes('\n' + constants.QUEUE_DELIMITER + '\n'))
    os.write(queue_fd, body_block.SerializeToString())
    os.write(queue_fd, bytes('\n' + constants.QUEUE_DELIMITER + '\n'))
    sys.stdin = open('/tmp/queue.txt', 'rb')

  def test_read_blocks_from_queue(self):
    report_processor = dsrf_report_processor.BaseReportProcessor(
        dsrf_block_processor.BaseBlockProcessor())
    counter = 0
    for actual_block, expected_block in zip(
        report_processor.read_blocks_from_queue(),
        [BASIC_HEAD_BLOCK, BASIC_BODY_BLOCK]):
      counter += 1
      deserialized_block_str = unicode(actual_block).encode('utf-8').strip()
      self.assertMultiLineEqual(deserialized_block_str, expected_block.strip())
    self.assertEquals(counter, 2)


if __name__ == '__main__':
  unittest.main()
