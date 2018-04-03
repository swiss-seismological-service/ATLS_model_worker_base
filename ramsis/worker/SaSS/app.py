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

import sys
import traceback

from ramsis.worker import settings, utils
from ramsis.worker.SaSS import create_app
from ramsis.worker.utils.app import CustomParser, App, AppError
from ramsis.worker.utils.error import Error, ExitCode

__version__ = utils.get_version("SaSS")


class SaSSWorkerWebservice(App):
    """
    A webservice implementing the SaSS model.
    """

    def build_parser(self, parents=[]):
        """
        Set up the stationlite commandline argument parser.

        :param list parents: list of parent parsers
        :returns: parser
        :rtype: :py:class:`argparse.ArgumentParser`
        """
        parser = CustomParser(
            prog="eida-stationlite",
            description='Launch EIDA stationlite web service.',
            parents=parents)
        # optional arguments
        parser.add_argument('--version', '-V', action='version',
                            version='%(prog)s version ' + __version__)
        parser.add_argument('-p', '--port', metavar='PORT', type=int,
                            default=5000,
                            help='server port')

        return parser

    # build_parser ()

    def run(self):
        """
        Run application.
        """
        exit_code = ExitCode.EXIT_SUCCESS.value
        try:
            app = self.setup_app()
            self.logger.info('Serving with local WSGI server.')
            app.run(threaded=True, debug=True, port=self.args.port)

        except Error as err:
            self.logger.error(err)
            exit_code = ExitCode.EXIT_ERROR.value
        except Exception as err:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.logger.critical('Local Exception: %s' % err)
            self.logger.critical('Traceback information: ' +
                                 repr(traceback.format_exception(
                                     exc_type, exc_value, exc_traceback)))
            exit_code = ExitCode.EXIT_ERROR.value

        sys.exit(exit_code)

    # run ()

    def setup_app(self):
        """
        Setup and configure the Flask app with its API.

        :returns: The configured Flask application instance.
        :rtype :py:class:`flask.Flask`:
        """
        app_config = {
            'PORT': self.args.port, }
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
            settings.PATH_RAMSIS_WORKER_CONFIG,
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
