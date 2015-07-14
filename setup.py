import os
import sys

if sys.version_info[:2] < (2, 4) or sys.version_info[0] > 2:
    msg = ("SuperlanceAdds requires Python 2.4 or later but does not work on "
           "any version of Python 3.  You are using version %s.  Please "
           "install using a supported version." % sys.version)
    sys.stderr.write(msg)
    sys.exit(1)

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.md')).read()
except (IOError, OSError):
    README = ''

setup(name='superlanceadds',
      version='0.1.2-dev',
      license='BSD-derived (http://www.repoze.org/LICENSE.txt)',
      description='sesmail superlance plugin for supervisord',
      long_description=README,
      classifiers=[
          "Development Status :: 3 - Alpha",
          'Environment :: No Input/Output (Daemon)',
          'Intended Audience :: System Administrators',
          'Natural Language :: English',
          'Operating System :: POSIX',
          'Topic :: System :: Boot',
          'Topic :: System :: Monitoring',
          'Topic :: System :: Systems Administration',
      ],
      data_files=[('/etc', ['superlanceadds/superlanceadds.conf'])],
      author='Sumit Kumar',
      author_email='sumitkumar1209@gmail.com',
      maintainer="Sumit Kumar",
      maintainer_email="sumitkumar1209@gmail.com",
      url='http://github.org/sumitkumar1209',
      keywords='supervisor monitoring aws ec2',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'supervisor',
      ],
      tests_require=[
          'supervisor',
          'mock',
      ],
      test_suite='superlanceadds.tests',
      entry_points="""\
      [console_scripts]
      sesmail = superlanceadds.sesmail:main
      """
      )
