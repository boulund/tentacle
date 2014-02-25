Customizing modules in Tentacle
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Tentacle is constructed using a modular approach making it easy
to customize and modify. A common modification or addition to 
Tentacle could be to add support for an additional mapping software.

Creating/modifying mapper modules
*********************************

Within the Tentacle folder structure, the mapper modules are 
located in `$TENTACLE_ROOT/tentacle/mappers`. Mapper modules
inherit from the base mapper class

.. automodule:: tentacle.mappers.mapper
    :members:
    :undoc-members:
    :show-inheritance:
