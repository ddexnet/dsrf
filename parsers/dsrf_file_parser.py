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

"""Parses a single flat file to a list of block objects.

The input of this component is a single file from a ddex report, and a list of
cell and row validators.
The output is a list of protocol buffer block objects.
"""
import csv
import gzip
from os import path
import sys

from dsrf import constants
from dsrf import error
from dsrf.parsers import dsrf_schema_parser
from dsrf.proto import block_pb2
from dsrf.proto import cell_pb2
from dsrf.proto import row_pb2


class TsvDialect(csv.Dialect):
  delimiter = constants.FILE_DELIMITER
  quotechar = ''
  escapechar = constants.ESCAPER
  doublequote = False
  skipinitialspace = False
  lineterminator = '\n'
  quoting = csv.QUOTE_NONE


class DSRFFileParser(object):
  """Parses a single file in the DSRF report."""

  def __init__(self, logger, dsrf_xsd_file, avs_xsd_file, file_path):
    """Initializes the File Parser.

    Args:
      logger: dsrf_logger.DSRFLogger object
      dsrf_xsd_file: Optional user-provided path to custom XSD.
      avs_xsd_file: Optional user-provided path to custom AVS XSD.
      file_path: Path to the .tsv[.gz] file to parse.
    """
    self.logger = logger
    self.dsrf_xsd_file = dsrf_xsd_file
    self.avs_xsd_file = avs_xsd_file
    self.file_path = file_path
    self.file_name = path.basename(file_path)
    # Will be set when we parse the XSD
    self.row_validators_list = None

  def get_block_number(self, line, row_number):
    """Returns the line block number if it exists.

    Args:
      line: The line from the file to parse.
      row_number: The line number in the file.

    Returns:
      The block number which appears in the line.
    """
    try:
      return int(line[1])
    except (IndexError, ValueError):
      raise error.RowValidationFailure(
          row_number, self.file_name,
          'The block id "%s" in line number %s was expected to be an integer.'
          % (line[1].upper(), row_number))

  def get_cell_object(self, cell_validator, cell_parsed_data):
    """Parses the cell data to a protocol buffer cell object.

    Args:
      cell_validator: Instance of a subclass of
                      cell_validators.BaseCellValidator.
      cell_parsed_data: The data from the cell, either an integer, float, string
        or boolean.

    Returns:
      A cell_pb2.Cell object.
    """
    cell_proto = cell_pb2.Cell(
        name=cell_validator.cell_name, cell_type=cell_validator.get_cell_type())
    if not isinstance(cell_parsed_data, list):
      cell_parsed_data = [cell_parsed_data]
    if cell_proto.cell_type == cell_pb2.STRING:
      cell_proto.string_value.extend(cell_parsed_data)
    elif cell_proto.cell_type == cell_pb2.INTEGER:
      cell_proto.integer_value.extend(cell_parsed_data)
    elif cell_proto.cell_type == cell_pb2.DECIMAL:
      cell_proto.decimal_value.extend(cell_parsed_data)
    elif cell_proto.cell_type == cell_pb2.BOOLEAN:
      cell_proto.boolean_value.extend(cell_parsed_data)
    return cell_proto

  def get_row_object(self, line, row_type, row_number, block_number):
    """Parses the row data to a protocol buffer row object.

    Args:
      line: The row from the file (eg. ['FFOO', '123']).
      row_type: String row type (eg. 'SY02', 'SY0201').
      row_number: The row number which is now parsed in the original file.
      block_number: The number of the block, for error reporting purposes.

    Returns:
      A row_pb2.Row object.
    """
    row = row_pb2.Row(type=row_type, row_number=row_number)
    if not self.row_validators_list:
      sys.stderr.write(
          '\n' + constants.COLOR_RED +
          'Schema parsing was unsuccessful. Please check the log file at '
          + self.logger.log_file_path + constants.ENDC + '\n')
      sys.exit(-1)
    row_validator = self.row_validators_list[row_type]
    cells = []
    for cell_validator, cell_content in zip(row_validator, line):
      if not cell_validator:
        continue
      cell_parsed_data = cell_validator.validate_value(
          cell_content, row_number, self.file_name, block_number)
      # If cell_parsed_data is None, it means the cell either contained an
      # invalid value, or was empty.
      if cell_parsed_data not in (None, ''):
        cells.append(self.get_cell_object(cell_validator, cell_parsed_data))
    row.cells.extend(cells)
    return row

  def is_compressed(self):
    return self.file_name.endswith(constants.GZIP_COMPRESSED_FILE_SUFFIX)

  def _get_row_type(self, line, row_number):
    """Returns the type of the row.

    Args:
      line: The line to parse.
      row_number: The line number of the parsed line.

    Returns:
      A 4-6 character row type code (eg. "MW01", "SY0201").
    """
    if not line:
      raise error.RowValidationFailure(
          row_number, self.file_name,
          'It is not permissible to include empty Records.')
    row_type = line[0].upper()
    if constants.VERSIONED_TSV_ROW_TYPE_PATTERN.match(row_type):
      # We have a row type of the form "SY02.01", convert to "SY0201".
      row_type = row_type.replace('.', '')
    if self.row_validators_list and row_type not in self.row_validators_list:
      raise error.RowValidationFailure(
          row_number, self.file_name,
          'Row type %s does not exist in the XSD. Valid row types are: %s. ' % (
              row_type, self.row_validators_list.keys()))
    return row_type

  def get_row_validators(self, row):
    """Parses the row validators from the XSD.

    XSD is either user-specified or inferred from the HEAD row.

    Returns:
      row_validators_list:
         A list of subclass of cell_validators.BaseCellValidator.
        (eg. [[string_validator, decimal_validator],[string_validator]]).
    """
    dsrf_xsd_file = self.dsrf_xsd_file
    if not dsrf_xsd_file:
      # User did not specify one, read from the library.
      profile_name, profile_version = row[2:4]
      self.logger.info(
          'Detected profile and version from HEAD: %s (%s)' %
          (profile_name, profile_version))
      try:
        dsrf_xsd_file = constants.get_xsd_file(profile_name, profile_version)
      except ValueError as e:
        sys.stderr.write(str(e))
        sys.exit(-1)

    self.logger.info('XSD file location: %s' % dsrf_xsd_file)

    schema_parser = dsrf_schema_parser.DsrfSchemaParser(
        self.avs_xsd_file, dsrf_xsd_file)
    return schema_parser.parse_xsd_file(self.logger)

  def parse_file(self, file_number):
    """Parses the file to a protocol buffer block objects.

    Args:

      file_number: The file number in the report (eg. "3of4" -> 3).

    Yields:
      Each yield is a single block object (block_pb2.Block).
    """
    row_number = 0
    block_number = 0
    if self.is_compressed():
      tsv = gzip.open(self.file_path, 'rU')
    else:
      tsv = open(self.file_path, 'rU')
    current_block = block_pb2.Block(file_number=file_number)
    self.logger.info(
        'Start parsing the HEAD block in file number %s.', file_number)
    for line in csv.reader(tsv, dialect=TsvDialect):
      row_number += 1
      # Comment row.
      if line[0].startswith(constants.COMMENT_SIGN):
        continue
      try:
        row_type = self._get_row_type(line, row_number)
        # End of block check.
        if self.is_end_of_block(line, row_type, row_number, current_block):
          yield current_block
          current_block = block_pb2.Block(file_number=file_number)
        # HEAD/FOOT row.
        if (constants.HEADER_ROW_PATTERN.match(row_type) or
            row_type in constants.FOOT_ROWS):
          current_block.type = block_pb2.HEAD
          if row_type in constants.FOOT_ROWS:
            self.logger.info(
                'Start parsing the FOOT block in file number %s.', file_number)
            current_block.type = block_pb2.FOOT
          if row_type == 'HEAD':
            self.row_validators_list = self.get_row_validators(line)
            current_block.version = line[1]
          current_block.rows.extend([
              self.get_row_object(line, row_type, row_number, block_number)])
          continue
        # Body row.
        block_number = self.get_block_number(line, row_number)
        row = self.get_row_object(line, row_type, row_number, block_number)
        if not current_block.type:
          current_block.type = block_pb2.BODY
          current_block.number = block_number
          self.logger.info('Start parsing block number %s in file number %s.',
                           block_number, file_number)
        current_block.rows.extend([row])
      except error.ValidationError as e:
        self.logger.error(e)

    yield current_block

  def is_end_of_block(self, line, row_type, row_number, current_block):
    # If the block is part of the header (HEAD or a summary row), we need to
    # check if we're still in the header.
    if current_block.type == block_pb2.HEAD:
      return not constants.HEADER_ROW_PATTERN.match(row_type)
    # Foot block is always the last one in a file.
    elif current_block.type == block_pb2.FOOT:
      return row_type not in constants.FOOT_ROWS
    # Cases of a FOOT block after a BODY block or 2 BODY blocks.
    else:
      return (
          row_type in constants.FOOT_ROWS or
          current_block.number != self.get_block_number(line, row_number))
