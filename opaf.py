####################################################################
## felipe.andres.manzano@gmail.com  http://feliam.wordpress.com/  ##
## twitter.com/feliam        http://www.linkedin.com/in/fmanzano  ##
####################################################################
'''
= Opaf! It's an Open PDF Analysis Framework! =

A pdf file rely on a complex file structure constructed from a set tokens, and grammar rules. Also each token being potentially compressed, encrypted or even obfuscated. 
*Open PDF Analysis Framework* will understand, decompress, de-obfuscate this basic pdf elements soup and present the resulting clean xml_pdf to a set of configurable rules for them to decide what to keep, what to cut out and ultimately if it is safe to open the resulting pdf projection.

It's in an early stage but more or less it should do something like this...
  # Scanner/Lexer                
      * Scan basic tokens                         `[done]`
      * Skip coments                              `[done]`
      * Position tracking                         `[done]`
  # Parser  
      * Rrules for basic types                    `[done]`
      * Rules for complete filestruct             `[done]`
      * Generate XML                              `[done]`
  # Xref Check                                    `[procastinated]`
      * Random acces crazy parsing                `[procastinated]`      
  # Fix references pass                           `[done]`
  # Expand streams  
      * FlateDecode                               `[done]`
      * LZWDecode                                 `[done]`
      * ASCIIHexDecode                            `[done]`
      * ASCII85Decode                             `[done]`        
      * RunLengthDecode                           `[done]`
      * Predictors 1...12                         `[done]`
      * JPEG2000                                  `[procastinated]`
      * DCTDecode                                 `[procastinated]`
      * CCITTFax                                  `[procastinated]`
                 
  # Analyze dissected PDF
  # Apply XPATH-like filter rules
      * XML in place
      * Tranformations over the XML
      * Need to generalize it XPATH function decorator  
        

'''

import logging
from optparse import OptionParser
import sys,math,traceback
from opaflib import *


if __name__ == '__main__':
    parser = OptionParser()
#    parser.add_option("-f", "--file", dest="pdf_filename",
#                      help="The input pdf file", metavar="PDF")

    parser.add_option("-x", "--xmlfile", dest="xml_filename",
                      help="Generate an xml file.", metavar="XML")

    parser.add_option("-l", "--logfile", dest="log_file", default='opaf.log',
                      help="Dump log messages to LOG file.", metavar="LOG")

    parser.add_option("-i", "--interactive", action="store_true", dest="shell", default=False,
                      help="Throw interactive python shell")

    parser.add_option("-g", "--graph", dest="graph", default='graph.png',
                      help="Generate and dump graph to GRAPH.", metavar="GRAPH")

    parser.add_option("-d", "--decompress", action="store_true", dest="decompress",
                      help="Apply a filter pack to decompress and parse objec streams.")



    (options, args) = parser.parse_args()
    logging.basicConfig(filename=options.log_file,level=logging.DEBUG)
    logger = logging.getLogger("OPAF")
    logger.debug("Starting OPAF")

    try:
        #load the especified pdf
        if len(args)>0 :
            filename=args[0]
            logger.info("Loading %s ..."%filename) 
            pdf = file(filename,"r").read()            
        else:
            assert options.interact == False, "Interactive not compatible with stdin feed"
            pdf = file("/dev/sdtin","r").read()            

        #Interact if asked
        if options.shell:
            raise "Uninmplemented"

        if pdf:
            #parse
            #fallback chain of different type of parsing algorithms
            logger.info("Parsing parsing parsing ...") 
            xml_pdf = None
            if xml_pdf == None:
                xml_pdf = normalParser(pdf)
            if xml_pdf == None:
                logger.info("PDF is NOT a sequence of objects as it SHALL be, for discussion see http://bit.ly/coRMtc")
                xml_pdf = bruteParser(pdf)
            if xml_pdf == None:
                xml_pdf = xrefParser(pdf)
            if xml_pdf == None:
                logger.info("Couldn't parse it. Damn!")
                    
        if options.decompress and xml_pdf:
            #A prepared script that flatten and fix the xml pdf.
            doEverything(xml_pdf)
            logger.info("We reach %d indirect objects!"%len(xml_pdf.xpath('//*[ starts-with(local-name(),"indirect_object")] ')))

        if options.xml_filename and xml_pdf:
            logger.info("Writing XML in %s"%options.xml_filename)            
            file('output.xml','w').write(getXML(xml_pdf))

        if options.graph and xml_pdf:
            logger.info("Generating GRAPH")
            graph(xml_pdf,options.graph)

    except Exception,e:
        print "OH!\n", e
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)


