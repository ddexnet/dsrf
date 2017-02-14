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

"""The library conformance tool."""

import argparse
import sys

from dsrf import constants
from dsrf.conformance import conformance_validators
from dsrf.conformance import error
from dsrf.conformance import xsd_profile_parser
from dsrf.processor import dsrf_block_processor
from dsrf.processor import dsrf_report_processor
from dsrf.proto import block_pb2


class ConformanceBlockProcessor(dsrf_block_processor.BaseBlockProcessor):

  def __init__(self):
    super(ConformanceBlockProcessor, self).__init__()
    # Will be set when we parse the XSD
    self.node = None

  def process_block(self, block):
    if block.type == block_pb2.BODY:
      return conformance_validators.validate_node(
          self.node, block.rows, 0, block.number, block.file_number)
    else:
      # For now we do not validate the header
      return 0


class ConformanceReportProcessor(dsrf_report_processor.BaseReportProcessor):
  """Processor for validating conformance."""

  def __init__(self, dsrf_xsd_file_name):
    self.dsrf_xsd_file_name = dsrf_xsd_file_name
    # Will be set when the HEAD block comes in.
    self.profile_name = None
    self.profile_version = None
    super(ConformanceReportProcessor, self).__init__(
        ConformanceBlockProcessor())

  def parse_profile_info_from_head(self, block):
    if block.type != block_pb2.HEAD:
      return
    for cell in block.rows[0].cells:
      if cell.name == 'Profile':
        self.profile_name = cell.string_value[0]
      elif cell.name == 'ProfileVersion':
        self.profile_version = cell.string_value[0]

  def parse_xsd(self, block):
    self.parse_profile_info_from_head(block)
    if not self.dsrf_xsd_file_name:
      # User did not provided an XSD to validate with.
      self.dsrf_xsd_file_name = constants.get_xsd_file(
          self.profile_name, self.profile_version)

    xsd_parser = xsd_profile_parser.XSDProfileParser(self.dsrf_xsd_file_name)
    self.block_processor.node = xsd_parser.parse_profile_from_xsd(
        self.profile_name)

  def process_report(self):
    nr_rows_validated = 0
    nr_blocks_validated = 0
    for block in self.read_blocks_from_queue():
      if not self.block_processor.node:
        self.parse_xsd(block)

      sys.stderr.write(
          constants.COLOR_GREEN + '\r[Block conformance] Blocks validated: %s '
          '(rows validated: %s)' % (
              nr_blocks_validated, nr_rows_validated) + constants.ENDC)
      nr_rows_validated += self.block_processor.process_block(block)
      nr_blocks_validated += 1
    return nr_blocks_validated, nr_rows_validated


if __name__ == '__main__':
  arg_parser = argparse.ArgumentParser(
      description='Validates the conformance of the report blocks.')
  arg_parser.add_argument(
      '--dsrf_xsd_file', type=str,
      help='The dsrf xsd schema file. This file contains the profiles and the '
      'blocks definition.')
  arg_parser.add_argument(
      '--dsrf_version', type=float,
      default=constants.DEFAULT_VERSION, help='The format version')
  args = arg_parser.parse_args()
  conformance_processor = ConformanceReportProcessor(args.dsrf_xsd_file)
  try:
    nr_blocks, nr_rows = conformance_processor.process_report()
  except error.BlockConformanceFailure as e:
    sys.stderr.write(
        constants.COLOR_RED + constants.BOLD + '\n[Conformance validation] '
        + str(e) + conformance_validators.QUANTIFIER_STR + constants.ENDC)
    sys.exit(-1)
  if nr_blocks > 0 and nr_rows > 0:
    print (constants.BOLD + constants.COLOR_GREEN +
           '\nThe conformance validation passed successfully! Validated %s '
           'blocks (%s rows).' % (nr_blocks, nr_rows)
           + constants.ENDC)
