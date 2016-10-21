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

"""The DSRF parsing library logger object."""

from collections import defaultdict
import logging

from dsrf import error


class DSRFLogger(logging.getLoggerClass()):
  """A logger object.

  Attributes:
    _counts: A dictionary storing a count for each log level.
    logger: The logging object (from the logging library).
    fail_fast: If true, an exception will be raised when the error method
               will be called.
    log_file_path: The log file name.
  """

  def __init__(self, module, log_file_path, fail_fast=False):
    super(DSRFLogger, self).__init__('')
    self.first_error = None
    self._counts = defaultdict(int)
    self.fail_fast = fail_fast
    self.logger = logging.getLogger(module)
    self.log_file_path = log_file_path
    logging.basicConfig(
        filename=log_file_path, filemode='w', level=logging.DEBUG)
    logging.setLoggerClass(DSRFLogger)

  def error(self, msg, *args, **kwargs):
    self.logger.error(msg, *args, **kwargs)
    self._counts['error'] += 1
    if self._counts['error'] == 1 and msg:
      self.first_error = str(msg)
    if self.fail_fast:
      raise msg

  def info(self, msg, *args, **kwargs):
    self._counts['info'] += 1
    self.logger.info(msg, *args, **kwargs)

  def warning(self, msg, *args, **kwargs):
    self._counts['warn'] += 1
    self.logger.warning(msg, *args, **kwargs)

  def raise_if_fatal_errors_found(self):
    if 'error' in self._counts:
      error_msg = (
          'Found %s fatal error(s) and %s warnings, please check log file at '
          '"%s" for details.\n' % (
              self._counts['error'], self._counts['warn'], self.log_file_path))
      if self.first_error:
        error_msg += 'First error: %s\n' % self.first_error
      raise error.ReportValidationFailure(error_msg)

