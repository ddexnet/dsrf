# DSRF Library: Change Log

## Version 1.1.0
* Library is refactored to support per-profile schemas, in the structure:
    ```
    schemas/
      ├── avs/
      │   ├── 1.0/
      │   │   └── read.me
      │   ├── 1.1/
      │   │   └── avs.xsd
      │   └── current/
      │       └── avs.xsd
      ├── AudioVisualProfile/
      │   └── 1.0/
      │       └── AudioVisualProfile.xsd
      └── UgcProfile/
   ```
* Schemas are now installed with the library and read from the installation
  directory.


## Version 1.0.9
* Includes a new schema (http://ddex.net/xml/dsrf/3/20161109):
  * Changed the royalty reporting profile to accurately reflect the standard.
  * Made sure that all data types for the RecordTypes are now called RecordType_XXXX[.xx].


## Version 1.0.8
* When conformance validation fails, include the row number of the last row that
  was validated successfully. Although not guaranteed to be accurate, this helps
  identify bad input.


## Version 1.0.7
* Fix ServiceDescription validation to allow any value in the filename if
  multiple different ServiceDescriptions are present in the SYxx rows.
* Allow empty values in repeated cells, eg. "|ISNI::0000000063037346"


## Version 1.0.6
* Fix for XSD parser to allow element definitions in any order.


## Version 1.0.5
* Allow any string in TerritoryOfUseOrSale (in the input filename).
* Log the version of the library that is being run.
* Change behavior to replace log file with each run, instead of appending.


## Version 1.0.4
* This CHANGELOG is added.
* Includes a new schema (http://ddex.net/xml/dsrf/3/20160915).
* A "RecordType-" prefix is now used for all record (row) type definitions in the XSD. This will decrease future code maintenance.
* Includes a fix to properly validate xs:duration values.
* Add a filename to the block proto and pass it through to the report processor.


## Version 1.0.3
* Includes a new schema (http://ddex.net/xml/dsrf/3/20160819).
* Library now supports versioned row types (eg. "SY02.01").
* Parser is updated to support agreed-upon TSV dialect (as documented at https://kb.ddex.net/display/DSRF30Arch/6.6.4+Communicating+Delimiters).


## Version 1.0.2
* First version uploaded to Github.
