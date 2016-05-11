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

"""Tests for dsrf_file_parser."""

from os import path
import unittest

from google.protobuf import text_format

from dsrf import dsrf_logger
from dsrf import error
from dsrf.parsers import cell_validators
from dsrf.parsers import dsrf_file_parser
from dsrf.proto import block_pb2
from dsrf.proto import cell_pb2
from dsrf.proto import row_pb2


def read_test_block(file_name):
  return open(
      path.join(path.dirname(__file__), '../testdata/blocks/' + file_name),
      'r').read()

HEAD_BLOCK = read_test_block('basic_head_block.txt')
BODY_BLOCK = read_test_block('basic_body_block.txt')
FOOT_BLOCK = read_test_block('basic_foot_block.txt')


class FileParserTest(unittest.TestCase):

  def setUp(self):
    self.maxDiff = None  # Allow self.assertMultiLineEqual to show all diffs.
    self.logger = dsrf_logger.DSRFLogger(__name__, '/tmp/example.log', True)
    self.row_validators_list = {
        'FHEA': [
            cell_validators.StringValidator('RecordType', self.logger, False),
            cell_validators.StringValidator('MessageId', self.logger, False),
            cell_validators.IntegerValidator('FileNumber', self.logger, False),
            cell_validators.IntegerValidator('NumberOfFiles', False, False)],
        'SY03': [
            cell_validators.StringValidator('RecordType', self.logger, False),
            cell_validators.StringValidator(
                'CommercialModelType', self.logger, False),
            cell_validators.StringValidator('UseType', self.logger, False),
            cell_validators.StringValidator('Territory', self.logger, False),
            cell_validators.StringValidator(
                'ServiceDescription', self.logger, False),
            cell_validators.IntegerValidator(
                'NumberOfUsages', self.logger, False)],
        'RE01': [
            cell_validators.StringValidator('RecordType', self.logger, False),
            cell_validators.StringValidator('BlockId', self.logger, False),
            cell_validators.StringValidator(
                'ReleaseReference', self.logger, False),
            cell_validators.StringValidator(
                'DspReleaseId', self.logger, False)],
        'AS02': [
            cell_validators.StringValidator('RecordType', self.logger, False),
            cell_validators.StringValidator('BlockId', self.logger, False),
            cell_validators.StringValidator(
                'ResourceReference', self.logger, False),
            cell_validators.StringValidator(
                'DspResourceId', self.logger, False),
            cell_validators.StringValidator('ISRC', self.logger, False),
            cell_validators.StringValidator('Title', self.logger, False)],
        'FFOO': [
            cell_validators.StringValidator('RecordType', self.logger, False),
            cell_validators.IntegerValidator(
                'NumberOfLines', self.logger, False)]
    }
    self.expected_blocks = [
        self.block_from_ascii(HEAD_BLOCK),
        self.block_from_ascii(BODY_BLOCK),
        self.block_from_ascii(FOOT_BLOCK)]

  def test_get_block_number_valid(self):
    valid_row = ['AS02', '3', 'RES2', 'of:e574ecc9b29949b782cf3e4b82f83bdd',
                 'USWWW0124570', 'Dread River (Jordan River)']
    parser = dsrf_file_parser.DSRFFileParser(self.logger, 'filename')
    self.assertEquals(parser.get_block_number(valid_row, 3), 3)

  def test_get_block_number_invalid(self):
    invalid_row = ['AS02', 'BL3', 'RES2',
                   'of:e574ecc9b29949b782cf3e4b82f83bdd', 'USWWW0124570',
                   'Dread River (Jordan River)']
    parser = dsrf_file_parser.DSRFFileParser(self.logger, 'filename')
    self.assertRaisesRegexp(
        error.RowValidationFailure,
        'Row number 3 \\(file=filename\\) is invalid \\(error=The block id "BL'
        '3" in line number 3 was expected to be an integer.\\)',
        parser.get_block_number, invalid_row, 3)

  def test_get_cell_object(self):
    cell_validator = cell_validators.StringValidator('ServiceDescription',
                                                     False, False)
    cell = cell_pb2.Cell()
    cell.name = 'ServiceDescription'
    cell.cell_type = cell_pb2.STRING
    cell.string_value.append('yt')
    parser = dsrf_file_parser.DSRFFileParser(self.logger, 'filename')
    self.assertEquals(parser.get_cell_object(cell_validator, 'yt'), cell)

  def setup_foot_row(self):
    row = row_pb2.Row(type='FFOO', row_number=8)
    record_type_cell = cell_pb2.Cell(
        name='RecordType', cell_type=cell_pb2.STRING, string_value=['FFOO'])
    number_of_lines_cell = cell_pb2.Cell(
        name='NumberOfLines', cell_type=cell_pb2.INTEGER, integer_value=[123])

    row.cells.extend([record_type_cell, number_of_lines_cell])
    return row

  def test_get_row_object(self):
    file_row = ['FFOO', '123']
    parser = dsrf_file_parser.DSRFFileParser(self.logger, 'filename')
    self.assertEquals(
        parser.get_row_object(
            [cell_validators.StringValidator('RecordType', self.logger, False),
             cell_validators.IntegerValidator(
                 'NumberOfLines', self.logger, False)],
            file_row, 8, 1),
        self.setup_foot_row())

  def test_get_row_object_invalid(self):
    file_row = ['FFOO', '123a']
    parser = dsrf_file_parser.DSRFFileParser(self.logger, 'filename')
    self.assertRaisesRegexp(
        error.CellValidationFailure,
        r'Cell "NumberOfLines" contains invalid value "123a". Value was '
        r'expected to be an integer. \[Block: 1, Row: 8, file=filename\]',
        parser.get_row_object, [
            cell_validators.StringValidator(
                'RecordType', self.logger, False),
            cell_validators.IntegerValidator(
                'NumberOfLines', self.logger, False)],
        file_row, 8, 1)

  @classmethod
  def block_from_ascii(cls, text):
    """Returns Block protobuf parsed from ASCII text."""
    block = block_pb2.Block()
    text_format.Merge(text, block)
    return block

  def test_is_end_of_block_false(self):
    first_line = ['HEAD', '123']
    new_block = block_pb2.Block()
    parser = dsrf_file_parser.DSRFFileParser(self.logger, 'filename')
    self.assertFalse(
        parser.is_end_of_block(first_line, 5, new_block))

  def test_is_end_of_block_true(self):
    line = ['SU02', 'BL8', '11', 'SR1', 'AdSupport', 'NonInterStream']
    new_block = block_pb2.Block()
    parser = dsrf_file_parser.DSRFFileParser(self.logger, 'filename')
    self.assertTrue(
        parser.is_end_of_block(line, 5, new_block))

  def test_get_row_type_valid(self):
    line = ['AS02', 'BL8', '11', 'SR1', 'AdSupport', 'NonInterStream']
    parser = dsrf_file_parser.DSRFFileParser(self.logger, 'filename')
    self.assertEquals(
        parser._get_row_type(
            line, self.row_validators_list, 3), 'AS02')

  def test_get_row_type_invalid(self):
    line = ['AB12', '8', '11', 'SR1', 'AdSupport', 'NonInterStream']
    parser = dsrf_file_parser.DSRFFileParser(self.logger, 'file_name')
    self.assertRaisesRegexp(
        error.RowValidationFailure,
        'Row number 3 \\(file=file_name\\) is invalid \\(error=Row type AB12 '
        'does not exist in the XSD. Valid row types are:',
        parser._get_row_type, line, self.row_validators_list, 3)

  def test_parse_uncompressed_file(self):
    filename = path.join(
        path.dirname(__file__), '../testdata/test_file_parser.tsv')
    parser = dsrf_file_parser.DSRFFileParser(self.logger, filename)
    for expected, actual in zip(
        self.expected_blocks, parser.parse_file(self.row_validators_list, 1)):
      self.assertMultiLineEqual(str(expected), str(actual))
      self.assertEquals(self.logger._counts['error'], 0)
      self.assertEquals(self.logger._counts['warn'], 0)
      self.assertTrue(self.logger._counts['info'] > 0)

  def test_parse_compressed_file(self):
    filename = path.join(
        path.dirname(__file__), '../testdata/test_file_parser.tsv.gz')
    parser = dsrf_file_parser.DSRFFileParser(self.logger, filename)
    for expected, actual in zip(
        self.expected_blocks, parser.parse_file(self.row_validators_list, 1)):
      self.assertMultiLineEqual(str(expected), str(actual))
      self.assertEquals(self.logger._counts['error'], 0)
      self.assertEquals(self.logger._counts['warn'], 0)
      self.assertTrue(self.logger._counts['info'] > 0)


if __name__ == '__main__':
  unittest.main()
