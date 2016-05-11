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

"""Calculates the report's AllocatedAmount, filtered by RightsController.
"""
import argparse
import sys

from dsrf import constants
from dsrf.processor import dsrf_block_processor
from dsrf.processor import dsrf_report_processor
from dsrf.proto import block_pb2


def _write_output(block_count, currency, allocated_amount_sum):
  sys.stderr.write(
      constants.BOLD +
      '\rBlocks processed: %s, Revenue: %s %s' % (
          block_count, currency, allocated_amount_sum) +
      constants.ENDC)


def _get_cell(row, name, decimal=False):
  """Retrieves a cell from a row by name."""
  for cell in row.cells:
    if cell.name == name:
      if decimal:
        return cell.decimal_value[0]
      return cell.string_value[0]


class AllocatedAmountBlockProcessor(dsrf_block_processor.BaseBlockProcessor):
  """Calculates the rights controller's revenue in a block."""

  def process_row(self, row, rights_controller_name):
    if _get_cell(row, 'RightsController') == rights_controller_name:
      return _get_cell(row, 'AllocatedAmount', decimal=True)
    return 0.0

  def get_currency_from_head(self, summary_record, rights_controller_name):
    """Extracts the currency from an SY02 row."""
    if _get_cell(summary_record, 'RightsController') == rights_controller_name:
      return  _get_cell(summary_record, 'Currency')
    return ''

  def validate_rights_controller_name(self, rights_controller_name, head_block):
    """Validates that the rightscontroller is actually in the file."""
    summary_records = [row for row in head_block.rows if row.type == 'SY02']
    rights_controllers = [
        str(_get_cell(row, 'RightsController'))
        for row in summary_records]

    if rights_controller_name not in rights_controllers:
      sys.stderr.write(
          'Rights Controller "%s" not found in the report. Rights '
          'controllers present in the report: %r\n' % (
              rights_controller_name, rights_controllers))

  def process_block(self, block, rights_controller_name):
    """Returns the given rights controller's revenue in the block.

    Returns the AllocatedAmount for the rights controller name.

    Args:
      block: A block_pb2.Block object to process.
      rights_controller_name: The name for the revenue processing.

    Returns:
      A tuple of a non-negative integer with the rights controller's revenue,
      the currency.
    """
    block_amount = 0
    block_currency = ''
    if block.type == block_pb2.HEAD:
      self.validate_rights_controller_name(rights_controller_name, block)
      for row in block.rows:
        if _get_cell(row, 'RightsController') != rights_controller_name:
          continue
        if row.type == 'SY02':
          block_currency = self.get_currency_from_head(
              row, rights_controller_name)
    elif block.type == block_pb2.BODY:
      for row in block.rows:
        if _get_cell(row, 'RightsController') != rights_controller_name:
          continue
        if row.type == 'LI01':
          block_amount += self.process_row(row, rights_controller_name)

    return block_amount, block_currency


class CalculateAllocatedAmount(dsrf_report_processor.BaseReportProcessor):

  def __init__(self, rights_controller_name):
    super(CalculateAllocatedAmount, self).__init__(
        AllocatedAmountBlockProcessor())
    self.rights_controller_name = rights_controller_name

  def process_report(self):
    """Calculates the rights controller's revenue in the report.

    Returns the sum of the AllocatedAmount for the given rights
    controller name.

    Returns:
      A tuple of a non-negative integer with the rights controller's revenue,
      the currency.
    """
    block_count = 0
    allocated_amount_sum = 0.0
    currency = ''
    for block in self.read_blocks_from_queue():
      block_count += 1
      row_amount, row_currency = self.block_processor.process_block(
          block, self.rights_controller_name)
      if not currency:
        currency = row_currency
      allocated_amount_sum += row_amount
      _write_output(block_count, currency, allocated_amount_sum)
    return allocated_amount_sum, currency


if __name__ == '__main__':
  arg_parser = argparse.ArgumentParser(
      description='Calculates the revenue for a rights controller name.')
  arg_parser.add_argument('rights_controller_name', type=str)
  args = arg_parser.parse_args()
  report_processor = CalculateAllocatedAmount(args.rights_controller_name)
  amount, currency_ = report_processor.process_report()
  sys.stderr.write(
      constants.BOLD + constants.COLOR_GREEN +
      '\nTotal revenue: %s %s\n' % (amount, currency_) +
      constants.ENDC)
