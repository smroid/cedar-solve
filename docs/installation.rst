Installation
============

Getting Python
--------------
Cedar-solve is written for Python 3.7 or later (and therefore runs on almost any platform) and should
work with most modern Python 3 installations. There are many ways to get Python on your system.
Most easily, by going to `the python webiste <https://www.python.org/>`_ and selecting your
platform. On many operating systems Python is installed by default, but this can be a very old
version (often 2.7). Check if you have something installed by running ``python --version`` in a
command prompt or terminal window. You can also check ``python3 --version`` as it is sometimes
installed under this name. In the latter case, use ``python3`` and ``pip3`` in place of ``python``
and ``pip`` in these instructions.

Getting Cedar-solve
--------------
Cedar-solve is not available on PyPI (the Python Package Index) yet. Instead you need to provide
a link to or download the GitHub source code.

Use PIP to download and install
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The easiest method is to let PIP download from GitHub and install. This will set up all
dependencies and make the package usable from anywhere.::

    pip install git+https://github.com/smroid/cedar-solve.git

You can test that it works by running the example provided in the GitHub repo.

Manually download source code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Go to `the GitHub repository <https://github.com/smroid/cedar-solve>`_, click `Clone or Download` and
`Download ZIP` and extract the cedar-solve directory to where you want to use it. You can put this
directly in your Python project as a module and use, or see below for how to install it.

Use git to download and contribute to source code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To be able to easily download and contribute updates to cedar-solve you should install Git. Follow the
instructions for your platform `over here <https://git-scm.com/downloads>`_.

Now open a terminal/CMD window in the directory where you wish to use cedar-solve and clone the
GitHib repository::

    git clone "https://github.com/smroid/cedar-solve.git"

You should see the cedar-solve directory created for you with all neccessary files. Check the status of
your repository by typing::

    cd cedar-solve
    git status

which should tell you that you are on the branch "master" and are up to date with the origin (which
is the GitHub version of cedar-solve). If a new update has come to GitHub you can update yourself by
typing::

    git pull

If you wish to contribute (please do!) and are not familiar with Git and GitHub, start by creating
a user on GitHub and setting you username and email::

    git config --global user.name "your_username_here"
    git config --global user.email "email@domain.com"

You will now also be able to push proposed changes to the software. There are many good resources
for learning about Git, `the documentation <https://git-scm.com/doc>`_ which includes the reference,
a free book on Git, and introductory videos is a good place to start.

Installing from source
^^^^^^^^^^^^^^^^^^^^^^
Open a command prompt or terminal and navigate to the project repository root directory.

Create a virtual environment in the root of the repository to work in::

    python -m venv .venv

Activate the virtual environment::

    # linux, macos
    source .venv/bin/activate

    # windows cmd
    venv\Scripts\activate.bat

    # windows powershell
    venv\Scripts\Activate.ps1

To install the project for local development::

    pip install -e ".[dev,docs,cedar-detect]"

This will install all dependencies into the virtual environment. You can
test that it works by running the example::

    cd examples
    python test_tetra3.py

which should print out the solutions for the included test images.

You can run the automated test suite with this command (from the repository root dir)::

    pytest

    # skip slow tests
    pytest -m "not slow"

Using cedar-solve as a module in your repository

A specific branch named `no_big_files` is available for practical inclusion as a git submodule
in your own repository. This does not include the default database and example images, making
it less than 1 MB. For a specific application you probably want a custom database anyway.

If problems arise
-----------------
Please get in touch by `filing an issue <https://github.com/smroid/cedar-solve/issues>`_.
