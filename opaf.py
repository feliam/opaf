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
logging.basicConfig(filename='opaf.log',level=logging.DEBUG)
logger = logging.getLogger("OPAF")
logger.debug("Starting OPAF")

import re,sys,math,traceback
from opaflib import *

if __name__ == '__main__':
    try:
        pass
#        import psyco
#        psyco.full()
    except:
        pass

    bytes = 0
    files = 0
    for filename in sys.argv[1:] :
        try:
            logger.info("Analyzing %s ..."%filename) 
            pdf = file(filename,"r").read()            
            files += 1
            bytes += len(pdf)

            #fallback chain of different type of parsing algorithms
            xml_pdf = None
            if xml_pdf == None:
                xml_pdf = normalParser(pdf)
            if xml_pdf == None:
                logger.info("PDF is NOT a sequence of objects as it SHALL be, for discussion see http://bit.ly/coRMtc")
                xml_pdf = bruteParser(pdf)
            if xml_pdf == None:
                xml_pdf = xrefParser(pdf)
                

            #A prepared script that flatten and fix the xml pdf.
            doEverything(xml_pdf)
            logger.info("We reach %d indirect objects!"%len(xml_pdf.xpath('//*[ starts-with(local-name(),"indirect_object")] ')))


            logger.info("Writing XML in output.xml")            
            file('output.xml','w').write(getXML(xml_pdf))

            logger.info("Generating GRAPH")
            graph(xml_pdf)

        except Exception,e:
            print "OH!\n", e
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)


