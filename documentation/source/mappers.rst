Customizing modules in Tentacle
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Tentacle is constructed using a modular approach making it easy to customize
and modify. A common modification or addition to Tentacle could be to add
support for an additional mapping software.


.. _adding mappers:

Creating/modifying mapper modules
*********************************

Within the Tentacle folder structure, the mapper modules are located in
``$TENTACLE_ROOT/tentacle/mappers``. If Tentacle was installed using ``pip``
into a virtualenv, the mapper modules must be placed (or symlinked) in
``$TENTACLE_VENV/lib/python2.7/site-packages/tentacle/mappers`` so that
Tentacle can find them. Do not forget to add an import line in the
``tentacle/mappers/__init__.py`` as well!

Mapper modules inherit from the base mapper class, as seen in the example
mapper modules that are provided with Tentacle. To create a new mapper module,
copy one of the others, change the filename and modify it to suit your mapper.
Make sure that the mapper you want to use is available in your ``PATH``
variable.

Another important aspect to consider when adding support for an additional mapper 
is that there needs to be a parser that can extract the information Tentacle 
requires from the mapper's output files. All such parsers are located in the submodule
``tentacle.parsers``. See :ref:`parsers`.

Generic mapper class for Tentacle
=================================
.. automodule:: tentacle.mappers.mapper
    :members:
    :undoc-members:
    :show-inheritance:
