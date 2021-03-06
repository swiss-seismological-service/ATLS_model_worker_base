# This is <setup.py>
# ----------------------------------------------------------------------------
#
# Copyright (c) 2018 by Daniel Armbruster (SED, ETHZ),
#                       Lukas Heiniger (SED, ETHZ)
#
# setup.py (ramsis.worker)
#
# REVISIONS and CHANGES
# 2018/04/03    V1.0   Daniel Armbruster
#
# ============================================================================
"""
setup.py for ramsis.worker

.. note:

    Packaging is performed by means of `Python namespace packages
    <https://packaging.python.org/guides/packaging-namespace-packages/>`_
"""

import os
import sys
from setuptools import setup


if sys.version_info[:2] < (3, 6):
    raise RuntimeError("Python version >= 3.6 required.")


def get_version(filename):
    from re import findall
    with open(filename) as f:
        metadata = dict(findall("__([a-z]+)__ = '([^']+)'", f.read()))
    return metadata['version']

# get_version ()


_authors = [
    'Lukas Heiniger',
    'Walsh Alexander',
    'Daniel Armbruster']
_authors_email = [
    'lukas.heiniger@sed.ethz.ch',
    'daniel.armbruster@sed.ethz.ch']

_install_requires = [
    'Flask>=0.12.2',
    'Flask-RESTful>=0.3.6',
    'webargs>=2.1',
    "ramsis.utils==0.1", ]

_extras_require = {'doc': [
    "epydoc==3.0.1",
    "sphinx==1.4.1",
    "sphinx-rtd-theme==0.1.9", ]}

_tests_require = []

_dependency_links = [(
    "git+https://gitlab.seismo.ethz.ch/indu/ramsis.utils.git"
    "#egg=ramsis.utils-0.1"), ]

_data_files = [
    ('', ['LICENSE'])]

_entry_points_sass = {
    'console_scripts': [
        'ramsis-worker-sass = ramsis.worker.SaSS.app:main', ]}
_entry_points = _entry_points_sass.copy()

_name = 'ramsis.worker'
_version = get_version(os.path.join('ramsis', 'worker', '__init__.py'))
_description = ('RT-RAMSIS worker component.')
_packages = ['ramsis.worker',
             'ramsis.worker.utils',
             'ramsis.worker.SaSS', ]

subsys = sys.argv[1]
if subsys == 'SaSS':
    sys.argv.pop(1)

    _version = get_version(os.path.join('ramsis', 'worker', 'SaSS',
                                        '__init__.py'))

    _description = ('Model SaSS from the RT-RAMSIS worker component.')
    # TODO(damb): adjust includes/excludes
    _packages = ['ramsis.worker',
                 'ramsis.worker.utils',
                 'ramsis.worker.SaSS', ]
    _entry_points = _entry_points_sass


# ----------------------------------------------------------------------------
setup(
    name=_name,
    # TODO(damb): Provide version string globally
    version=_version,
    author=' (SED, ETHZ),'.join(_authors),
    author_email=', '.join(_authors_email),
    description=_description,
    license='AGPL',
    keywords=[
        'induced seismicity',
        'risk',
        'risk assessment',
        'risk mitigation',
        'realtime',
        'seismology'],
    url='https://gitlab.seismo.ethz.ch/indu/ramsis.worker.git',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Science/Research',
        ('License :: OSI Approved :: GNU Affero '
            'General Public License v3 or later (AGPLv3+)'),
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Scientific/Engineering', ],
    platforms=['Linux', ],
    packages=_packages,
    data_files=_data_files,
    dependency_links=_dependency_links,
    install_requires=_install_requires,
    extras_require=_extras_require,
    tests_require=_tests_require,
    include_package_data=True,
    zip_safe=False,
    entry_points=_entry_points
    # TODO(damb): test_suite=unittest.TestCase
)

# ----- END OF setup.py -----
