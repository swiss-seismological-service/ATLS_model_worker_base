# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Initialize a RT-RAMSIS worker DB.
"""

import sys
import traceback

from sqlalchemy import create_engine

from ramsis.utils.app import CustomParser, App, AppError
from ramsis.utils.error import Error, ExitCode
from ramsis.sfm.worker import orm
from ramsis.sfm.worker.utils import url
from ramsis.sfm.em1.core.parser import default_params

__version__ = '0.1'


# ----------------------------------------------------------------------------
class DBInitApp(App):
    """
    Utility application initializing :py:mod:`ramsis.sfm.worker` specific DBs.
    """
    def build_parser(self, parents=[]):
        """
        Set up the commandline argument parser.

        :param list parents: list of parent parsers
        :returns: parser
        :rtype: :py:class:`argparse.ArgumentParser`
        """
        parser = CustomParser(
            prog="ramsis.sfm.worker-db-init",
            description='Initialize a DB for RT-RAMSIS workers.',
            parents=parents)
        # optional arguments
        parser.add_argument('--version', '-V', action='version',
                            version='%(prog)s version ' + __version__)
        parser.add_argument('--force', '-f', action='store_true',
                            default=False,
                            help='Ignore existent DB schemas.')

        # positional arguments
        parser.add_argument('db_url', type=url, metavar='URL',
                            help=('DB URL indicating the database dialect and '
                                  'connection arguments. For SQlite only a '
                                  'absolute file path is supported.'))

        return parser

    def run(self):
        """
        Run application.
        """
        exit_code = ExitCode.EXIT_SUCCESS
        try:
            engine = create_engine(self.args.db_url)

            if self.args.force:
                self.logger.debug(
                    'Force mode enabled. Drop existing DB model.')
                orm.ORMBase.metadata.drop_all(engine)

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


# ----------------------------------------------------------------------------
def main():
    """
    :py:class:`ramsis.sfm.worker.utils.db.DBInitApp` wrapper.
    """

    app = DBInitApp(log_id='RAMSIS')
    defaults = default_params('ws_params')
            
    try:
        app.configure(
            defaults['PATH_RAMSIS_WORKER_CONFIG'],
            positional_required_args=['db_url'])
    except AppError as err:
        # handle errors during the application configuration
        print('ERROR: Application configuration failed "%s".' % err,
              file=sys.stderr)
        sys.exit(ExitCode.EXIT_ERROR.value)

    return app.run()


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()
