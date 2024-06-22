Installation
============

Getting Python
--------------
Cedar-solve is written for Python 3.8 or later (and therefore runs on almost any platform) and should
work with most modern Python 3 installations. There are many ways to get Python on your system.
Most easily, by going to `the python website <https://www.python.org/>`_ and selecting your
platform. On many operating systems Python is installed by default, but this can be a very old
version (often 2.7). Check if you have something installed by running ``python --version`` in a
command prompt or terminal window. You can also check ``python3 --version`` as it is sometimes
installed under this name. In the latter case, use ``python3`` and ``pip3`` in place of ``python``
and ``pip`` in these instructions.

Getting Cedar-solve
-------------------
Cedar-solve is available on PyPI (the Python Package Index). You may install it by::

    pip install cedar-solve

You can test that it works by invoking the database generator command::

    tetra3-gen-db --help

Example
^^^^^^^
An `example <https://github.com/smroid/cedar-solve/blob/master/examples/test_tetra3.py>`_ is available on the GitHub repository showing some ways of working with the library.

Manually download source code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You have two options to manually download the source code.

1. Download the release of your choice by going to `GitHub Releases <https://github.com/smroid/cedar-solve/releases>`_
and downloading the `Source Code` archive in your preferred format.

2. Download the latest code from the `GitHub repository <https://github.com/smroid/cedar-solve>`_. Click `Clone or Download` and
`Download ZIP`

Afterward you can extract the cedar-solve directory to where you want to use it.

Use git to download and contribute to source code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To be able to easily download and contribute updates to cedar-solve you should install Git. Follow the
instructions for your platform `over here <https://git-scm.com/downloads>`_.

Now open a terminal/CMD window in the directory where you wish to use cedar-solve and clone the
GitHib repository::

    git clone "https://github.com/smroid/cedar-solve.git"

You should see the cedar-solve directory created for you with all necessary files. Check the status of
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

    # run all tests
    pytest

    # skip slow tests
    pytest -m "not slow"

If problems arise
-----------------
Please get in touch by `filing an issue <https://github.com/smroid/cedar-solve/issues>`_.

You can also join the `Cedar Discord <https://discord.gg/xbDrUyXP>`_ server.
