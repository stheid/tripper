===================================
TRipper - a Tatort download utility
===================================

The software downloads `Tatort`_ episodes from the mediathek.
The tool is aimed for people that want to create a local collection of all episodes.

TRipper comes with two data-wrappers:

1. Mediathekview - to retrieve the available episodes and their download urls

2. Wikipedia - to retrieve the metadata


Future releases will therefore also come with a scheduler such that the tool can run peridodicly.

The implementation heavily relies on ffmpeg and youtube-dl (as a python dependency)

Special thanks to the folkes at `mediathekview`_ for providing an easy to use api.

.. _`Tatort`: https://en.wikipedia.org/wiki/Tatort
.. _`mediathekview`: https://mediathekviewweb.de

Installation
============

::

  $ apt install ffmpeg # (or similar commands)
  $ pip install git+git://github.com/stheid/tripper.git


Usage
=====

Adapt the :code:`config.yaml` to your liking and run the program.

::

  $ tripper


Roadmap
=======

1. Add sheduler to execute the downloader regularly

2. Add docker image


