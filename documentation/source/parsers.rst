.. _parsers:

=======
Parsers
=======

Tentacle contains several parsers that parse input files to produce the data
structures required to hold the results (coverage, counts) but also parsers for
the output files from mappers (e.g. gem, razers3, or blast tabular formats).

If additional mappers are to be added to the program, suitable parsers might also
be required. Have a look at how the supplied parsers are implemented and 
write something similar for the specific format you require. Make sure to add
the parser to the ``tentacle.parsers.__init__py``. 



Parsers module
**************

Mapper output parsers
=====================

blast8 tabular format
---------------------
.. automodule:: tentacle.parsers.blast8
    :members:
    :undoc-members:
    :show-inheritance:

GEM format
----------
.. automodule:: tentacle.parsers.gem
    :members:
    :undoc-members:
    :show-inheritance:

RazerS3 format
--------------
.. automodule:: tentacle.parsers.razers3
    :members:
    :undoc-members:
    :show-inheritance:

SAM format
----------
.. automodule:: tentacle.parsers.sam
    :members:
    :undoc-members:
    :show-inheritance:

Parser to create coverage data structure
========================================

.. automodule:: tentacle.parsers.initialize_contig_data
    :members:
    :undoc-members:
    :show-inheritance:
