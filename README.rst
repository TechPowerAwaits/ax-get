==========
ax-get
==========
.. raw:: html

    <img src="https://img.shields.io/badge/code%20style-black-000000.svg", alt="code style: black">

This script downloads a specified version of Axelor ERP (both source code and WAR file). It automatically extracts them and on POSIX-like systems, attempts to chown them so they belong to the tomcat user and group.

------------


Requirements
------------
- `Python 3.6 or later <https://www.python.org/downloads/>`_
- `requests <https://pypi.org/project/requests/>`_

Poetry is used to install the dependencies. Click `here <https://python-poetry.org/docs/>`_ for instructions on how to install Poetry.

Running the script
------------------
Before running the script, if you haven't already, run:

::

    poetry install

inside the project directory. This will install all dependencies.


Then to run the actual script:

::

    poetry run ax-get [--src] <major> <minor> <patch>

License
-------
The script is licensed under the `0BSD <http://landley.net/toybox/license.html>`_.