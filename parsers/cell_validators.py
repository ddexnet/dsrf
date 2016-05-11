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

"""Objects to validate the cells in a Flat File."""

import re

from dsrf import constants
from dsrf import error
from dsrf.proto import cell_pb2


class BaseCellValidator(object):
  """Base validator class."""
  # The human-readable type of the expected value in the cell. Used in
  # exceptions.
  _expected_value = ''

  def __init__(self, cell_name, logger, required=True, repeated=False):
    self.cell_name = cell_name
    self.logger = logger
    self.required = required
    self.repeated = repeated

  def validate_value(self, value, row_number, file_name, block_number):
    """Validates and parses the cell value.

    Args:
      value: The cell value, to validate.
      row_number: The cell's row number in the file.
      file_name: The cell's file name.
      block_number: Integer block number.

    Returns:
      The cell parsed cell value, if it fits the cell definition.
    """
    try:
      return self._validate_value(value, row_number, file_name, block_number)
    except error.CellValidationFailure as e:
      self.logger.error(e)

  def _validate_value(self, value, row_number, file_name, block_number):
    """Validates the cell values, by the validator definition.

    First check if the cell is required and repeated, and then validates a
    single value.

    Args:
      value: The cell value, to validate.
      row_number: The cell's row number in the file.
      file_name: The cell's file name.
      block_number: Integer block number.

    Returns:
      The cell parsed cell value, if it fits the cell definition.
    """
    # If the cell is required, it can't be empty.
    if not value:
      if self.required:
        raise error.RequiredCellMissing(
            self.cell_name, row_number, file_name, block_number, value,
            self.get_expected_value())
      else:
        return value
    if not self.repeated:
      return self.validate_single_value(
          value, row_number, file_name, block_number)
    validated_values = []
    for val in value.split(constants.REPEATED_VALUE_DELIMITER):
      validated_values.append(
          self.validate_single_value(val, row_number, file_name, block_number))
    return validated_values

  def validate_single_value(self, value, row_number, file_name, block_number):
    pass

  def get_expected_value(self):
    return self._expected_value

  def _raise_validation_failure(self, value, row_number, file_name,
                                block_number):
    raise error.CellValidationFailure(
        self.cell_name, row_number, file_name, block_number, value,
        self.get_expected_value())

  def get_cell_type(self):
    return None


class StringValidator(BaseCellValidator):
  """Validates String cells."""
  _expected_value = 'a string'

  def validate_single_value(self, value, row_number, file_name, block_number):
    if not isinstance(value, str):
      self._raise_validation_failure(value, row_number, file_name, block_number)
      return
    try:
      return unicode(value, 'utf-8')
    except UnicodeDecodeError as e:
      raise error.BadUnicodeError(
          self.cell_name, row_number, file_name, block_number, value, str(e))

  def get_cell_type(self):
    return cell_pb2.STRING


class IntegerValidator(BaseCellValidator):
  """Validates Integer cells."""
  _expected_value = 'an integer'

  def validate_single_value(self, value, row_number, file_name, block_number):
    try:
      if float(value).is_integer():
        if value.find('.') >= 0:
          self.logger.warning(
              'The cell %s in line number %s (file=%s) is a decimal (%s), but '
              'expected to be an integer.'
              % (self.cell_name, row_number, file_name, value))
        return int(float(value))
    except ValueError:
      pass
    self._raise_validation_failure(value, row_number, file_name, block_number)

  def get_cell_type(self):
    return cell_pb2.INTEGER


class BooleanValidator(BaseCellValidator):
  """Validates Boolean cells."""
  _expected_value = 'a boolean'

  def validate_single_value(self, value, row_number, file_name, block_number):
    try:
      if value.lower() in ['true', 'false']:
        return value.lower() == 'true'
    except AttributeError:
      pass
    self._raise_validation_failure(value, row_number, file_name, block_number)

  def get_cell_type(self):
    return cell_pb2.BOOLEAN


class DecimalValidator(BaseCellValidator):
  """Validates Decimal cells."""
  _expected_value = 'a decimal'

  def validate_single_value(self, value, row_number, file_name, block_number):
    try:
      return float(value)
    except ValueError:
      self._raise_validation_failure(value, row_number, file_name, block_number)

  def get_cell_type(self):
    return cell_pb2.DECIMAL


class PatternValidator(BaseCellValidator):
  """Validates cells with string pattern."""

  def __init__(self, pattern, cell_name, logger, required=True, repeated=False):
    super(PatternValidator, self).__init__(
        cell_name, logger, required, repeated)
    self.pattern = pattern
    self._expected_value = 'of the form "%s".' % self.pattern

  def validate_single_value(self, value, row_number, file_name, block_number):
    re_pattern = re.compile(self.pattern)
    try:
      if re_pattern.match(value):
        return value
    except TypeError:
      pass
    self._raise_validation_failure(value, row_number, file_name, block_number)

  def get_cell_type(self):
    return cell_pb2.STRING


class FixedStringValidator(BaseCellValidator):
  """Validates fixed string cells (enum)."""

  def __init__(
      self, valid_values, cell_name, logger, required=True, repeated=False):
    super(FixedStringValidator, self).__init__(
        cell_name, logger, required, repeated)
    self.valid_values = valid_values
    # Optimization for faster lookup
    self.valid_value_set = set(
        [valid_value.upper() for valid_value in valid_values])
    self._expected_value = 'one of the following: %s' % self.valid_values

  def validate_single_value(self, value, row_number, file_name, block_number):
    try:
      if value.upper() in self.valid_value_set:
        return value.upper()
    except AttributeError:
      pass
    self._raise_validation_failure(value, row_number, file_name, block_number)

  def get_cell_type(self):
    return cell_pb2.STRING


class DurationValidator(PatternValidator):
  """Validates 'xs:duration' cells."""

  def __init__(self, cell_name, logger, required=True, repeated=False):
    super(DurationValidator, self).__init__(
        constants.DURATION_PATTERN, cell_name, logger, required, repeated)
    self._expected_value = 'ISO 8601 duration'


class DateTimeValidator(PatternValidator):
  """Validates 'xs:dateTime' cells."""

  def __init__(self, cell_name, logger, required=True, repeated=False):
    super(DateTimeValidator, self).__init__(
        constants.DATETIME_PATTERN, cell_name, logger, required, repeated)
    self._expected_value = 'ISO 8601 dateTime'
