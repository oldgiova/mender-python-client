# Copyright 2021 Northern.tech AS
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
import logging
import threading

from mender.log.log import DeploymentLogHandler

log = logging.getLogger(__name__)


def setup(args):
    handlers = []
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(
        logging.Formatter(
            datefmt="%Y-%m-%d %H:%M:%S",
            fmt="%(module)-15s %(threadName)-20s-%(thread_id)-3s "
            + "%(asctime)s %(levelname)-8s %(message)s",
        )
    )
    stream_handler.addFilter(thread_id_filter)
    handlers.append(stream_handler)
    level = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }.get(args.log_level, logging.INFO)
    syslogger = (
        logging.NullHandler() if args.no_syslog else logging.handlers.SysLogHandler()
    )
    handlers.append(syslogger)
    if args.log_file:
        handlers.append(logging.FileHandler(args.log_file))

    deployment_log_handler = DeploymentLogHandler()
    handlers.append(deployment_log_handler)

    mender_logger = logging.getLogger("mender")
    mender_logger.deployment_log_handler = deployment_log_handler
    mender_logger.handlers = handlers
    mender_logger.setLevel(level)
    log.info(f"Log level set to {logging.getLevelName(level)}")


def thread_id_filter(record):
    record.thread_id = threading.get_native_id()
    return record
