# This is <app.py>
# -----------------------------------------------------------------------------
#
# Purpose: SaSS worker application facilities.
#
# Copyright (c) Daniel Armbruster (SED, ETH), Lukas Heiniger (SED, ETH)
#
# REVISION AND CHANGES
# 2018/04/03        V0.1    Daniel Armbruster
# =============================================================================
"""
RAMSIS SaSS (Shapiro and Smothed Seismicity) worker.
"""

import argparse
import copy
import json
import sys
import traceback

from ramsis.utils.app import CustomParser, App, AppError
from ramsis.utils.error import Error, ExitCode
from ramsis.worker import settings as global_settings
from ramsis.worker.utils import escape_newline, url
from ramsis.worker.SaSS import __version__, create_app, settings


def model_defaults(config_dict):
    """
    Parse a default model configuration.

    :param str config_dict: Configuration dictionary
    :retval: dict
    """
    try:
        config_dict = json.loads(config_dict)
    except Exception:
        raise argparse.ArgumentTypeError(
            'Invalid model default configuration dictionary syntax.')

    def merge_dicts(dict1, dict2):
        """
        Merge values recursively from :code:`dict2` into :code:`dict1`.
        """
        for k in dict1.keys():
            if type(dict1[k]) is dict:
                merge_dicts(dict1[k], dict2[k])
            else:
                try:
                    dict1[k] = dict2[k]
                except KeyError:
                    pass

    # merge_dicts ()

    def validate_keys(dict1, dict2):
        """
        Validate recursively if keys of :code:`dict1` are in :code:`dict2`.
        """
        for k in dict1.keys():
            if k not in dict2:
                raise ValueError('Invalid key found: {!r}'.format(k))
            if type(dict1[k]) is dict:
                validate_keys(dict1[k], dict2[k])

    # validate_keys ()

    retval = copy.deepcopy(settings.RAMSIS_WORKER_SFM_DEFAULTS)
    try:
        validate_keys(config_dict, settings.RAMSIS_WORKER_SFM_DEFAULTS)
    except ValueError as err:
        raise argparse.ArgumentTypeError(err)

    merge_dicts(retval, config_dict)
    return retval

# model_defaults ()


class SaSSWorkerWebservice(App):
    """
    A webservice implementing the SaSS (Shapiro and Smothed Seismicity) model.
    """
    VERSION = __version__

    def build_parser(self, parents=[]):
        """
        Set up the commandline argument parser.

        :param list parents: list of parent parsers
        :returns: parser
        :rtype: :py:class:`argparse.ArgumentParser`
        """
        parser = CustomParser(
            prog="ramsis-worker-sass",
            description='Launch SaSS worker webservice.',
            parents=parents)
        # optional arguments
        parser.add_argument('-p', '--port', metavar='PORT', type=int,
                            default=settings.RAMSIS_WORKER_SASS_PORT,
                            help='server port')
        parser.add_argument('--model-defaults', metavar='DICT',
                            type=model_defaults, dest='model_defaults',
                            default=settings.RAMSIS_WORKER_SFM_DEFAULTS,
                            help=("Default model configuration parameter dict "
                                  "(JSON syntax). (default: %(default)s)"))

        # positional arguments
        parser.add_argument('db_url', type=url, metavar='URL',
                            help=('DB URL indicating the database dialect and '
                                  'connection arguments. For SQlite only a '
                                  'absolute file path is supported.'))

        return parser

    # build_parser ()

    def run(self):
        """
        Run application.
        """
        exit_code = ExitCode.EXIT_SUCCESS
        try:
            app = self.setup_app()
            self.logger.debug('Routes configured: {}'.format(
                escape_newline(str(app.url_map))))
            self.logger.debug(
                'Model defaults configured: {!r}'.format(
                    self.args.model_defaults))
            self.logger.info('Serving with local WSGI server.')
            app.run(threaded=True, debug=True, port=self.args.port)

        except Error as err:
            self.logger.error(err)
            exit_code = ExitCode.EXIT_ERROR
        except Exception as err:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.logger.critical('Local Exception: %s' % err)
            self.logger.critical('Traceback information: ' +
                                 repr(traceback.format_exception(
                                     exc_type, exc_value, exc_traceback)))
            exit_code = ExitCode.EXIT_ERROR

        sys.exit(exit_code.value)

    # run ()

    def setup_app(self):
        """
        Setup and configure the Flask app with its API.

        :returns: The configured Flask application instance.
        :rtype :py:class:`flask.Flask`:
        """
        app_config = {
            'PORT': self.args.port,
            'SQLALCHEMY_DATABASE_URI': self.args.db_url,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'RAMSIS_SFM_DEFAULTS': self.args.model_defaults
        }
        app = create_app(config_dict=app_config)

        return app

    # setup_app ()

# class SaSSWorkerWebservice


# ----------------------------------------------------------------------------
def main():
    """
    main function for SaSS model worker webservice
    """

    app = SaSSWorkerWebservice(log_id='RAMSIS-SASS')

    try:
        app.configure(
            global_settings.PATH_RAMSIS_WORKER_CONFIG,
            positional_required_args=['db_url'],
            config_section=settings.RAMSIS_WORKER_SASS_CONFIG_SECTION)
    except AppError as err:
        # handle errors during the application configuration
        print('ERROR: Application configuration failed "%s".' % err,
              file=sys.stderr)
        sys.exit(ExitCode.EXIT_ERROR.value)

    return app.run()

# main ()


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()

# ---- END OF <app.py> ----
