# DSRF Library: Change Log

## Version 1.0.4
* This CHANGELOG is added.
* Schema is updated to "http://ddex.net/xml/dsrf/3/20160915".
* A "RecordType-" prefix is now used for all record (row) type definitions in the XSD. This will decrease future code maintenance.
* Includes a fix to properly validate xs:duration values.
* Add a filename to the block proto and pass it through to the report processor.


## Version 1.0.3
* Includes a new schema (http://ddex.net/xml/dsrf/3/20160819).
* Library now supports versioned row types (eg. "SY02.01").
* Parser is updated to support agreed-upon TSV dialect (as documented at https://kb.ddex.net/display/DSRF30Arch/6.6.4+Communicating+Delimiters).


## Version 1.0.2
* First version uploaded to Github.
