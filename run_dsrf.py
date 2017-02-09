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

"""Run the DSRF library from a command line."""

import argparse
from os import path

from dsrf import constants
from dsrf.parsers import dsrf_report_manager


def file_path(file_name):
  return path.join(path.dirname(__file__), file_name)


def file_existance(file_name):
  return path.isfile(file_name)


def run_report_manager():
  """Parses the input and runs the report_manager."""
  arg_parser = argparse.ArgumentParser(description='Processes a dsrf report.')
  arg_parser.add_argument('files_list', nargs='+',
                          help='A list of files in the report.')
  arg_parser.add_argument(
      '--dsrf_xsd_file', type=str, help='The dsrf xsd schema file. This file '
      'contains the profiles and the row types definition.')
  arg_parser.add_argument(
      '--avs_xsd_file', type=str, help='The xsd avs schema file. This file '
      'contains the allowed value set to the fixed string cells.')
  arg_parser.add_argument(
      '--dsrf_version', type=float, default=constants.DEFAULT_VERSION,
      help='The format version')
  arg_parser.add_argument(
      '--log_file', type=str, default='/tmp/example.log',
      help='This file will contain the library logs.')
  arg_parser.add_argument(
      '--human_readable', type=bool, default=False, help='If True, write the'
      'block to the queue in a human readable form.')
  args = arg_parser.parse_args()

  dsrf_xsd_file = None
  if args.dsrf_xsd_file:
    dsrf_xsd_file = path.expanduser(args.dsrf_xsd_file)

  avs_xsd_file = None
  if args.avs_xsd_file:
    avs_xsd_file = path.expanduser(args.avs_xsd_file)

  if bool(avs_xsd_file) != bool(dsrf_xsd_file):
    raise Exception(
        'You either have to specify both --dsrf_xsd_file and --avs_xsd_file '
        '(to use custom XSDs) or neither (to use installed XSDs')

  log_file = None
  if args.log_file:
    log_file = path.expanduser(args.log_file)

  report_manager = dsrf_report_manager.DSRFReportManager(log_file)
  report_manager.parse_report(
      args.files_list, dsrf_xsd_file, avs_xsd_file, args.human_readable)


if __name__ == '__main__':
  run_report_manager()
