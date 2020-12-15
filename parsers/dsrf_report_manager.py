# Lint as: python2, python3
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
"""The dsrf library manager.

Parses a flat file report to verified block objects.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from collections import defaultdict
import os
from os import path
import sys

import six

from dsrf import constants
from dsrf import dsrf_logger
from dsrf import error
from dsrf.parsers import dsrf_file_parser
from dsrf.parsers import file_name_validators
from dsrf.parsers import report_files_validators
from dsrf.proto import block_pb2
from dsrf.proto import cell_pb2


def _get_version():
  try:
    # pylint: disable=g-import-not-at-top
    import pkg_resources
    from pkg_resources import get_distribution
  except ImportError:
    return '[Version Unknown - ImportError]'

  try:
    return 'v%s - %s' % (get_distribution('dsrf').version,
                         get_distribution('dsrf').location)
  except pkg_resources.DistributionNotFound:
    return '[Version Unknown - DistributionNotFound]'


def _raise_filename_validation_error(file_name, row_number, row_type, cell_name,
                                     cell_value, filename_part, filename_value,
                                     file_number):
  raise error.FileNameValidationFailure(
      file_name, '[%s: row %s]: The cell "%s" with the value "%s" does '
      'not match the file name part "%s" with the value "%s" in file '
      'number %s.' % (row_number, row_type, cell_name, cell_value,
                      filename_part, filename_value, file_number))


def _validate_party_filename(file_name, file_name_dict, party_cells,
                             party_type):
  """Message Sender/Recipient values in the filename must match the HEAD.

  Args:
    file_name: Original name of the file.
    file_name_dict: Components extracted from the filename.
    party_cells: The Party ID & name from the HEAD for the Sender|Receiver.
    party_type: Either 'Sender' or 'Recipient'
  """
  if (party_cells and
      file_name_dict['Message' + party_type] not in list(party_cells.values())):
    raise error.FileNameValidationFailure(
        file_name, 'The Message%(party_type)s value in the filename '
        '("%(filename_value)s") did not match either of the '
        '%(party_type)sPartyId ("%(party_id)s") or the %(party_type)sName '
        '("%(party_name)s") in the HEAD row' % {
            'party_type': party_type,
            'filename_value': file_name_dict['Message' + party_type],
            'party_id': party_cells[party_type + 'PartyId'],
            'party_name': party_cells[party_type + 'Name']
        })


class DSRFReportManager(object):
  """Manages the report parsing.

  Responsibilities:
  -Parsing / validating the flags.
  -Validating files name and size (basic validations).
  -Transferring the version flag to the DSRF schema parser.
  -Transferring the files and the validators to the DSRF File Parser.
  -Receiving the processed blocks objects from the DSRF File Parsers.
  -Validating the block numbers (unique per report).
  -Transferring the block objects to a queue.
  """

  def __init__(self, log_file_path):
    """Initializes the Report Manager.

    Args:
      log_file_path: The path of the log file, where the library logs will be
        written to.
    """
    self.logger = dsrf_logger.DSRFLogger('dsrf', log_file_path)
    self.logger.info('>>> Running DSRF Library %s <<<' % _get_version())

  def write_to_queue(self, block, logger, human_readable=False):
    """Writes the block object to the output queue.

    Override this if you want to change the queue form.

    Args:
      block: A block_pb2.Block object to write.
      logger: Logger object.
      human_readable: If True, write to the queue the block in a human readable
        form. Otherwise, Write the block as a raw bytes.
    """
    output = None
    if human_readable:
      output = six.ensure_binary(six.text_type(block), 'latin')
    else:
      output = block.SerializeToString()
    try:
      os.write(sys.stdout.fileno(), output)
      os.write(sys.stdout.fileno(), b'\n' + constants.QUEUE_DELIMITER + b'\n')
    except OSError as e:
      logger.exception('Could not write to queue: %s', e)
      sys.stderr.write(
          'WARNING: Parser interrupted. Some blocks were not parsed.\n')
      sys.exit(-1)

  @classmethod
  def validate_head_block(cls, block, file_name, file_name_dict):
    """Validates the file HEAD.

    Args:
      block: A block_pb2.Block object.
      file_name: The block file name.
      file_name_dict: A dictionary containing the different components of the
        filename, keyed by the component names.
                      (eg. {'x': 3, 'ext': 'tsv.gz'}).
    """
    message_recipient_cells = defaultdict(str)
    message_sender_cells = defaultdict(str)
    service_descriptions = dict()
    for row in block.rows:
      for cell in row.cells:
        if cell.name in constants.MESSAGE_RECIPIENT_MATCH:
          message_recipient_cells[cell.name] = cell.string_value[0]
        if cell.name in constants.MESSAGE_SENDER_MATCH:
          message_sender_cells[cell.name] = cell.string_value[0]
        if cell.name in constants.HEAD_CELLS_MATCH_TO_FILE_NAME_PARTS:
          filename_part = constants.HEAD_CELLS_MATCH_TO_FILE_NAME_PARTS[
              cell.name]
          if cell.cell_type == cell_pb2.INTEGER:
            if int(file_name_dict[filename_part]) not in cell.integer_value:
              _raise_filename_validation_error(file_name, row.type,
                                               row.row_number, cell.name,
                                               '%d' % cell.integer_value[0],
                                               filename_part,
                                               file_name_dict[filename_part],
                                               file_name_dict['x'])
          elif cell.cell_type == cell_pb2.STRING:
            if filename_part == 'ServiceDescription':
              service_descriptions[cell.string_value[0]] = (row, cell)
              continue
            if file_name_dict[filename_part] not in cell.string_value:
              _raise_filename_validation_error(file_name, row.type,
                                               row.row_number, cell.name,
                                               cell.string_value, filename_part,
                                               file_name_dict[filename_part],
                                               file_name_dict['x'])

    if len(service_descriptions) == 1:
      # There's only one type of ServiceDescription being communicated, it must
      # match the filename.
      row, cell = list(service_descriptions.values())[0]
      if file_name_dict['ServiceDescription'] not in service_descriptions:
        _raise_filename_validation_error(file_name, row.type, row.row_number,
                                         cell.name, cell.string_value,
                                         filename_part,
                                         file_name_dict[filename_part],
                                         file_name_dict['x'])

    _validate_party_filename(file_name, file_name_dict, message_recipient_cells,
                             'Recipient')

    _validate_party_filename(file_name, file_name_dict, message_sender_cells,
                             'Sender')
    block.filename = file_name

  def parse_report(self,
                   files_list,
                   dsrf_xsd_file,
                   avs_xsd_file,
                   human_readable=False,
                   write_head=True):
    """Parses a dsrf report to block objects.

    The blocks are transferred to the queue.

    Args:
      files_list: A list of files in the report to parse.
      dsrf_xsd_file: Optional user-provided path to custom XSD.
      avs_xsd_file: Optional user-provided path to custom AVS XSD.
      human_readable: If True, write the block to the queue in a human readable
        form. Otherwise, write the block as a raw bytes.
      write_head: If set to False, the header will not be written to the queue.

    Returns:
      dsrf_logger.DSRFLogger object.
    """
    file_path_to_name_map = {
        file_path: path.basename(file_path) for file_path in files_list
    }

    expected_components = constants.FILE_NAME_COMPONENTS
    self.logger.info('Validating the report file names.')
    report_validator = report_files_validators.ReportFilesValidator(
        file_name_validators.FileNameValidator(expected_components),
        self.logger)
    report_validator.validate_file_names(list(file_path_to_name_map.values()))
    blocks = defaultdict(set)
    for file_path, file_name in six.iteritems(file_path_to_name_map):
      file_parser = dsrf_file_parser.DSRFFileParser(self.logger, dsrf_xsd_file,
                                                    avs_xsd_file, file_path)
      file_name_dict = file_name_validators.FileNameValidator.split_file_name(
          file_name, expected_components)
      file_number = file_name_dict['x']
      self.logger.info('Start parsing file number %s.', file_number)
      for block in file_parser.parse_file(int(file_number)):
        if block.type == block_pb2.BODY:
          for compared_file_number, file_blocks in six.iteritems(blocks):
            if block.number in file_blocks:
              raise error.ReportValidationFailure(
                  'The block number %s is not unique. It appears in files '
                  'number: %s and %s.' %
                  (block.number, min(file_number, compared_file_number),
                   max(file_number, compared_file_number)))
          blocks[file_number].add(block.number)
        elif block.type == block_pb2.HEAD:
          try:
            self.validate_head_block(block, file_name, file_name_dict)
          except error.FileNameValidationFailure as e:
            self.logger.error(e)
          if not write_head:
            # Skip writing the header to the queue, if requested.
            continue
        else:
          # FOOT
          continue
        self.write_to_queue(block, self.logger, human_readable)
    try:
      self.logger.raise_if_fatal_errors_found()
    except error.ReportValidationFailure as e:
      sys.stderr.write(constants.COLOR_RED + constants.BOLD +
                       '\n[Cell validation] ' + str(e) + constants.ENDC)
    return self.logger
