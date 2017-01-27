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
from os import path
import sys

import pkg_resources

from dsrf import constants
from dsrf.conformance import conformance_validators
from dsrf.conformance import error
from dsrf.conformance import xsd_profile_parser
from dsrf.processor import dsrf_block_processor
from dsrf.processor import dsrf_report_processor
from dsrf.proto import block_pb2


class ConformanceBlockProcessor(dsrf_block_processor.BaseBlockProcessor):

  def __init__(self, node):
    super(ConformanceBlockProcessor, self).__init__()
    self.node = node

  def process_block(self, block):
    if block.type == block_pb2.BODY:
      return conformance_validators.validate_node(
          self.node, block.rows, 0, block.number, block.file_number)
    else:
      # For now we do not validate the header
      return 0


class ConformanceReportProcessor(dsrf_report_processor.BaseReportProcessor):

  def __init__(self, dsrf_xsd_file_name, profile_name):
    xsd_parser = xsd_profile_parser.XSDProfileParser(dsrf_xsd_file_name)
    profile_node = xsd_parser.parse_profile_from_xsd(profile_name)
    super(ConformanceReportProcessor, self).__init__(
        ConformanceBlockProcessor(profile_node))

  def process_report(self):
    nr_rows_validated = 0
    nr_blocks_validated = 0
    for block in self.read_blocks_from_queue():
      sys.stderr.write(
          constants.COLOR_GREEN + '\r[Block conformance] Blocks validated: %s '
          '(rows validated: %s)' % (
              nr_blocks_validated, nr_rows_validated) + constants.ENDC)
      nr_rows_validated += self.block_processor.process_block(block)
      nr_blocks_validated += 1
    return nr_blocks_validated, nr_rows_validated


def _get_xsd_file(dsrf_version):
  """Returns path to installed XSD, or local if no installed one exists."""
  schema_path = path.join('schemas', dsrf_version, 'sales-reporting-flat.xsd')
  installed_path = pkg_resources.resource_filename('dsrf', schema_path)
  try:
    # Verify file exists and is readable.
    with open(installed_path) as unused_fp:
      pass
  except IOError:
    # Fall back to local version
    local_path = path.join(path.dirname(__file__), '..', schema_path)
    sys.stderr.write(
        'Could not read installed XSD from %s. Using local version instead: %s'
        % (installed_path, local_path))
    return local_path

  return installed_path

if __name__ == '__main__':
  arg_parser = argparse.ArgumentParser(
      description='Validates the conformance of the report blocks.')
  arg_parser.add_argument(
      '--profile_name', type=str, required=True,
      help='The name of the profile to use in the conformance validation.')
  arg_parser.add_argument(
      '--dsrf_xsd_file', type=str,
      help='The dsrf xsd schema file. This file contains the profiles and the '
      'blocks definition.')
  arg_parser.add_argument(
      '--dsrf_version', type=float,
      default=constants.DEFAULT_VERSION, help='The format version')
  args = arg_parser.parse_args()
  if args.dsrf_xsd_file:
    dsrf_xsd_file = args.dsrf_xsd_file
  else:
    dsrf_xsd_file = _get_xsd_file(args.dsrf_version)
  conformance_processor = ConformanceReportProcessor(
      dsrf_xsd_file, args.profile_name)
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
