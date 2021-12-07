===================================
TRipper - a Tatort download utility
===================================

The software downloads `Tatort`_ episodes from the mediathek.
The tool is aimed for people that want to create a local collection of all episodes.

TRipper comes with two data-wrappers:

1. Mediathekview - to retrieve the available episodes and their download urls

2. Wikipedia - to retrieve the metadata


Future releases will therefore also come with a scheduler such that the tool can run peridodicly


.. _`Tatort`: https://en.wikipedia.org/wiki/Tatort

Installation
============

::

  $ pip install git+git://github.com/stheid/tripper.git


Usage
=====
::

  $ python -m tripper


Roadmap
=======

1. Add sheduler to execute the downloader regularly

2. Add docker image


