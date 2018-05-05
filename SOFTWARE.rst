===========================================
Software Development in St. Jarvis's Garden
===========================================

.. |holy-order| replace:: Holy Order of Saint Jarvis
.. _holy-order: https://github.com/Holy-Order-of-Saint-Jarvis

Modules
=======
Sometimes the question is less "what needs to be fixed" than "where can I even find this code?"
This section aims to help ameliorate said issue.

Core
----
These modules are written and maintained by the |holy-order|_.
They may need to be updated in the field and are expected to be runnable on a wide variety of platforms.

|rlyeh|_
   Tecthulu API and core types.

|garden-party|_
   Top-level code.
   This includes the core event loop, plugin manager, and CLI.

.. |rlyeh| replace:: ``rlyeh``
.. _rlyeh: https://github.com/Holy-Order-of-Saint-Jarvis/rlyeh
.. |garden-party| replace:: ``garden-party``
.. _garden-party: https://github.com/Holy-Order-of-Saint-Jarvis/garden-party

Plugins
-------
The software is intended to host plugins to drive each project that needs tech interaction.

**TBD**

Third-party
-----------

Critical dependencies
+++++++++++++++++++++

|openpixelcontrol|_
   RGB LED controller drivers.
   Used to control the |fadecandy|_ hardware for core resonator lighting.

|supervisord|_
   Application-level process manager.
   Used to control and monitor multiple processes.

.. |fadecandy| replace:: `fadecandy`
.. _fadecandy: https://github.com/scanlime/fadecandy
   
Core development utilities
++++++++++++++++++++++++++
These dependencies are important until the day of the event itself.
It should be possible to continue development on-site without them,
but it will likely be unpleasant.

|python-tecthulhu|_
   Tecthulu device simulator used for Camp Navarro 2017.
   Used for automated testing and validation.

.. |python-tecthulhu| replace:: ``python-tecthulhu``
.. |openpixelcontrol| replace:: ``openpixelcontrol``
.. |supervisord| replace:: ``supervisord``
.. _python-tecthulhu: https://github.com/terencehonles/python-tecthulhu
.. _openpixelcontrol: http://openpixelcontrol.org/
.. _supervisord: http://supervisord.org/

Transitive dependencies
-----------------------
To mitigate the risk of not having a binary package available for a given module,
all transitive dependencies *must* be tracked here.
Dependencies *should* be pinned using **setuptools**' ``install_requires`` option.

Transitive dependencies can be verified by running ``pipenv graph`` from a **properly-configured pipenv**.
The easiest way to ensure this proper configuration is to create a new pipenv specifically for a target package::

   $ git checkout https://github.com/Holy-Order-of-Saint-Jarvis/garden-party.git
   $ cd rlyeh
   $ touch Pipfile
   $ pipenv install '-e .'
   $ pipenv graph
   
Installing a package as the top-level target in a pipenv ensures that all dependencies are installed for discovery
by the ``graph`` subcommand.

The use of pipenv is intended to allow commiting ``Pipfile.lock`` just before departure for Navarro.
Freezing dependencies will ensure that any releases that may be picked up while on-site will not be deployed if the
environment is recreated.

::

   $ pipenv graph
   garden-party==18.5.0
     - attrs [required: >=17.4.0, installed: 18.1.0]
     - click [required: >=6.7, installed: 6.7]
     - rlyeh [required: >=18.4.0, installed: 18.4.0]
       - attrs [required: >=17.4.0, installed: 18.1.0]
       - requests [required: >=2.18.4, installed: 2.18.4]
         - certifi [required: >=2017.4.17, installed: 2018.4.16]
         - chardet [required: <3.1.0,>=3.0.2, installed: 3.0.4]
         - idna [required: >=2.5,<2.7, installed: 2.6]
         - urllib3 [required: <1.23,>=1.21.1, installed: 1.22]
**TBD**

**Note**: Once properly annotated, ``garden-party`` will include (and ideally pin) all other critical dependencies besides ``supervisor``.
At that point, this section can be streamlined with the ``rlyeh`` subsection entirely removed.
