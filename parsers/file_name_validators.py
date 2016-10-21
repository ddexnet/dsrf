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

"""Objects to validate a single file name in a dsrf report."""

from dsrf import constants
from dsrf import error


class FileNameValidator(object):
  """A single file name validator."""

  def __init__(self, expected_components):
    self.expected_components = expected_components

  def validate_value(self, file_name):
    """Validates that a filename consists of the expected components.

    Args:
      file_name: File name to validate.

    Returns:
      A dictionary of {component_name = component_value}
      (eg. {'ServiceDescription': 'AdSupport'}).
    """
    warnings = set()
    file_name_dict = self.split_file_name(file_name, self.expected_components)
    try:
      self.validate_xofy(file_name_dict['x'], file_name_dict['y'], file_name)
      self.validate_prefix(file_name_dict['DSR'], file_name,)
      self.validate_suffix(file_name_dict['ext'], file_name)
      self.validate_message_notification_period(
          file_name_dict['MessageNotificationPeriod'], file_name)
      self.validate_territory_of_use_or_sale(
          file_name_dict['TerritoryOfUseOrSale'], file_name)
      self.validate_message_created_datetime(
          file_name_dict['MessageCreatedDateTime'], file_name)
    except KeyError:
      raise error.FileNameValidationFailure(
          file_name, 'bad name structure, expected format: %s.' %
          constants.FILE_NAME_FORMAT)
    except error.FileNameValidationWarning as e:
      warnings.add(e)
    return file_name_dict, warnings

  @classmethod
  def validate_xofy(cls, x, y, file_name):
    try:
      if int(x) <= int(y):
        return x, y
    except ValueError:
      pass
    raise error.FileNameValidationFailure(
        file_name, 'File number is not an integer or does not exist.')

  @classmethod
  def validate_prefix(cls, prefix, file_name):
    if prefix != constants.FILE_NAME_PREFIX:
      raise error.FileNameValidationFailure(
          file_name, 'File name should start with %s.' %
          constants.FILE_NAME_PREFIX)
    return prefix

  @classmethod
  def validate_suffix(cls, suffix, file_name):
    if suffix not in constants.SUPPORTED_FILE_EXTENSIONS:
      raise error.FileNameValidationFailure(
          file_name, 'Suffix "%s" is not valid, supported suffixes: %s.' % (
              suffix, constants.SUPPORTED_FILE_EXTENSIONS))
    return suffix

  @classmethod
  def validate_message_notification_period(cls, mnp, file_name):
    if not constants.MESSAGE_NOTIFICATION_PERIOD_PATTERN.match(mnp):
      raise error.FileNameValidationFailure(
          file_name, 'Message Notification Period "%s" is invalid, should be '
          'ISO 8601:2004 period format.' % mnp)
    return mnp

  @classmethod
  def validate_territory_of_use_or_sale(cls, touos, file_name):
    """TerritoryOfUseOrSale may also be freeform, so this is just a warning."""
    if not constants.TERRITORY_OF_USE_OR_SALE_PATTERN.match(touos):
      raise error.FileNameValidationWarning(
          file_name,
          'It is recommended that the TerritoryOfUseOrSale be set to a '
          'CISAC TIS code or a two-letter ISO code (use "multi" or "worldwide" '
          'for multiple territories). Provided value: "%s"' % touos)
    return touos

  @classmethod
  def validate_message_created_datetime(cls, mcdt, file_name):
    if not constants.MESSAGE_CREATED_DATETIME_PATTERN.match(mcdt):
      raise error.FileNameValidationFailure(
          file_name, 'MessageCreated-DateTime "%s" is invalid, should be '
          'yyyyymmddThhmmss.' % mcdt)
    return mcdt

  @classmethod
  def split_file_name(cls, file_name, expected_components):
    """Splits the file name to a dictionary keyed by components names.

    Args:
      file_name: File name to split.
      expected_components: A list of the expected file name parts.

    Returns:
      A dictionary of the file name components names (keys) and the given file
      name parts (values).
    """
    basic_split = file_name.split(constants.FILE_NAME_DELIMITER)
    if len(basic_split) != len(constants.FILE_NAME_COMPONENTS) - 2:
      raise error.FileNameValidationFailure(
          file_name, 'bad name structure, expected format: %s.' %
          constants.FILE_NAME_FORMAT)
    xofy = basic_split[-2]
    message_created_time_ext = basic_split[-1]
    file_name_parts = basic_split[:-2]
    xofy = xofy.split('of')
    message_created_time_ext = message_created_time_ext.split('.', 1)
    file_name_parts.extend(xofy)
    file_name_parts.extend(message_created_time_ext)
    if len(file_name_parts) != len(constants.FILE_NAME_COMPONENTS):
      raise error.FileNameValidationFailure(
          file_name, 'bad name structure, expected format: %s.' %
          constants.FILE_NAME_FORMAT)
    file_name_dict = {component_name: value for component_name, value in
                      zip(expected_components, file_name_parts)}
    return file_name_dict
