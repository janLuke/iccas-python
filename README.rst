====================
ICCAS Python Helper
====================

..
    .. image:: https://img.shields.io/pypi/v/iccas.svg
            :target: https://pypi.python.org/pypi/iccas

.. image:: https://img.shields.io/travis/janLuke/iccas.svg
        :target: https://travis-ci.com/janLuke/iccas-python

..
    .. image:: https://readthedocs.org/projects/iccas/badge/?version=latest
            :target: https://iccas.readthedocs.io/en/latest/?badge=latest
            :alt: Documentation Status

This repository contains:

- a helper package to get the `ICCAS dataset`_ (Italian Coronavirus Cases by
  Age group and Sex) and work with it; this includes
- some Jupyter notebooks in the "notebooks" folder with some charts and tables.

The package includes several submodules:

.. list-table::
    :header-rows: 1
    :widths: 30 70

    * - Module
      - Description
    * - ``loading``
      - Obtain, cache and load the dataset(s)
    * - ``processing``
      - Data (pre)processing. Fix data inconsistencies, resample data with interpolation.
    * - ``queries``
      - Select subsets of data, aggregate or extract useful values.
    * - ``charts``
      - Draw charts and animations (in Italian or English).

* Free software: MIT license
* Documentation: https://iccas.readthedocs.io.

.. _`ICCAS dataset`: https://github.com/janLuke/iccas-dataset/


Installation
------------

To install the package::

    pip install iccas

If you want to use the CLI::

    pip install iccas[cli]

To run notebooks locally, you need to `install jupyter`_ , for example with::

    pip install jupyterlab

Then::

    pip install -r binder/requirements.txt
    ./binder/postBuild

.. _install jupyter: https://jupyter.org/install

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
