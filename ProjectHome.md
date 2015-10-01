# Opaf! It's an Open PDF Analysis Framework! #

A pdf file rely on a complex file structure constructed from a set tokens, and grammar rules. Also each token being potentially compressed, encrypted or even obfuscated.
**Open PDF Analysis Framework** will understand, decompress, de-obfuscate this basic pdf elements and present the resulting soup as a clean XML tree(done!).
From there a set of configurable rules can be used to decide what to keep, what to cut out and ultimately if it is safe to open the resulting pdf projection(50%done!).

INSTALLATION:
This is now available a pypi package on http://pypi.python.org/pypi/OPAF/
For install just do a
```
$easy_install opaf
```
Update: A windows installation screencast http://bit.ly/feJQf9

It has an embedded pdflib to generate pdfs.
It generates python scripts that generates the parsed pdf.
Etc..

### Its open source! HELP!! ###
Tasks:
  * Move the PLY lexer definition to a class (1) (2) (3)
  * Add test cases for each possible lexing token (1)(2)(4)
  * Generate the parsers from "python setup install" (5)
  * Make it possible to register and unregister Filters (6)
  * Improve and enforce the use of /DecodeParms and its defaults (6)
  * Test the PNG Predictors decoders. (6)
  * Add outsourcing filters for CCITT, JPEG, JBIG2, JPEG2k (6)
  * Define a class for opaflib "commands". (Organize all what is exported from opaflib/init.py) Commands that change the AST should be marked as different from the ones that just produce info (7)
  * Code the insanely stupid crypto thing of PDF spec. (**Trivial decryption of V4/AESV2 already done**) (7)(8)
  * Improve the graph generator so it contains more useful data (8)


  1. http://code.google.com/p/opaf/source/browse/trunk/opaflib/lexer.py
  1. http://feliam.wordpress.com/2010/08/06/lexing-pdf-just-for-the-un-fun-of-it/
  1. http://www.dabeaz.com/ply/ply.html#ply_nn17
  1. http://code.google.com/p/opaf/source/browse/trunk/#trunk%2Ftests
  1. http://code.google.com/p/opaf/source/browse/trunk/opaflib/parser.py
  1. http://code.google.com/p/opaf/source/browse/trunk/opaflib/filters.py
  1. http://code.google.com/p/opaf/source/browse/trunk/opaflib/__init__.py
  1. http://www.adobe.com/devnet/pdf/pdf_reference.html

http://about.me/feliam