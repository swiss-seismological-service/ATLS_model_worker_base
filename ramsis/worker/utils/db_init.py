# This is <db_init.py>
# -----------------------------------------------------------------------------
#
# Copyright (c) Daniel Armbruster (SED, ETH), Lukas Heiniger (SED, ETH)
#
# REVISION AND CHANGES
# 2018/08/17    V0.1    Daniel Armbruster
# =============================================================================
"""
Initialize a RT-RAMSIS worker DB.
"""

import sys
import traceback

from sqlalchemy import create_engine

from ramsis.utils.app import CustomParser, App, AppError
from ramsis.utils.error import Error, ExitCode
from ramsis.worker import settings
from ramsis.worker.utils import url, orm

__version__ = '0.1'


# ----------------------------------------------------------------------------
class DBInitApp(App):
    """
    Utility application initializing :py:mod:`ramsis.worker` specific DBs.
    """
    def build_parser(self, parents=[]):
        """
        Set up the commandline argument parser.

        :param list parents: list of parent parsers
        :returns: parser
        :rtype: :py:class:`argparse.ArgumentParser`
        """
        parser = CustomParser(
            prog="ramsis-worker-db-init",
            description='Initialize a DB for RT-RAMSIS workers.',
            parents=parents)
        # optional arguments
        parser.add_argument('--version', '-V', action='version',
                            version='%(prog)s version ' + __version__)

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
            engine = create_engine(self.args.db_url)

            # create db tables
            self.logger.debug('Creating database tables ...')
            orm.ORMBase.metadata.create_all(engine)

            self.logger.info(
                "DB '{}' successfully initialized.".format(self.args.db_url))

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

# class DBInit


# ----------------------------------------------------------------------------
def main():
    """
    :py:class:`ramsis.worker.utils.db.DBInitApp` wrapper.
    """

    app = DBInitApp(log_id='RAMSIS')

    try:
        app.configure(
            settings.PATH_RAMSIS_WORKER_CONFIG,
            positional_required_args=['db_url'],
            config_section=settings.RAMSIS_WORKER_DB_CONFIG_SECTION)
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

# ---- END OF <db_init.py> ----
