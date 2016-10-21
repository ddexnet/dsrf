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

"""Validates the report's file names."""

from dsrf import constants
from dsrf import error


class ReportFilesValidator(object):
  """Validates the report's file names."""

  def __init__(self, file_name_validator, logger):
    """Report files validator.

    Args:
        file_name_validator: file_name_validators.FileNameValidator object.
        logger: The library Logger object.
    """
    self.file_name_validator = file_name_validator
    self.logger = logger

  @classmethod
  def _raise_mismatch_parts(cls, part_name, expected_name, actual_name,
                            file_name):
    raise error.FileNameValidationFailure(
        file_name, 'The %s value "%s" is expected to match the other files'
        ' in the report and be "%s".' % (
            part_name, actual_name, expected_name))

  def validate_file_names(self, files_to_parse):
    """Validates the filenames' syntax to ensure they form a valid DSRF report.

    Args:
      files_to_parse: A list of filenames to validate.

    Returns:
      A dictionary of the files in the report. The key is the file number, and
      the value is the file name parts dictionary. (eg.
      {'1': {'DSR': 'DSR', 'MessageRecipient': 'PADPIDA2014999999Z',
              'MessageSender': 'PADPIDA2014111801Y',
              'ServiceDescription': 'AdSupport',
              'MessageNotificationPeriod': '2015-02',
              'TerritoryOfUseOrSale': 'AU', 'x': '1', 'y': '4',
              'MessageCreatedDateTime': '20150723T092522', 'ext': 'tsv.gz'
            }
      })
    """
    file_name_dicts = {}
    if not files_to_parse:
      self.logger.error(error.ReportValidationFailure(
          'Please provide a non-empty list of files.'))
    for file_name in sorted(files_to_parse):
      try:
        file_name_dict, warnings = self.file_name_validator.validate_value(
            file_name)
        for warning in warnings:
          self.logger.warning(warning)

        # Validate file number.
        file_number = file_name_dict['x']
        if file_number in file_name_dicts:
          raise error.ReportValidationFailure(
              'File number %s is not unique.' % file_number)
        if not file_name_dicts:
          # First file in the list, nothing to compare to yet.
          file_name_dicts[file_number] = file_name_dict
          continue
        compared_file = file_name_dicts.values()[0]
        file_name_dicts[file_number] = file_name_dict

        # Validate match file name parts.
        for match_part in constants.FILE_NAME_MATCH_PARTS:
          if compared_file[match_part] != file_name_dict[match_part]:
            self._raise_mismatch_parts(
                match_part, compared_file[match_part],
                file_name_dict[match_part], file_name)
      except error.ReportValidationFailure as e:
        self.logger.error(e)
    self.logger.raise_if_fatal_errors_found()
    report_files_number = file_name_dicts.values()[0]['y']
    for num in range(1, int(report_files_number) + 1):
      if str(num) not in file_name_dicts:
        raise error.ReportValidationFailure(
            'File number %s is missing in the report.' % num)

    return file_name_dicts
