####################################################################
## felipe.andres.manzano@gmail.com  http://feliam.wordpress.com/  ##
## twitter.com/feliam        http://www.linkedin.com/in/fmanzano  ##
####################################################################
import sys,re
import traceback

import ply.yacc as yacc
from opaf.lexer import tokens, LexerException # Get the token map from the lexer.  This is required.
from opaf.xmlast import create_node, payload, setpayload, expand_span, etree

#logging facility
import logging
#logging.basicConfig(filename='opaf.log',level=logging.DEBUG)
logger = logging.getLogger("PARSER")


#In PDF 1.5 and later, cross-reference streams may be used in 
#linearized files in place of traditional cross-reference tables.
#The logic described in this section, along with the appropriate 
#syntactic changes for cross-reference streams shall still apply.
def p_pdf(p):
    ''' pdf : HEADER pdf_update_list'''
    header = create_node('header',p.lexspan(1), p[1])
    p[0] = create_node('pdf', p.lexspan(0), "OPAF!", [header] + p[2])

#7.3.6    Array Objects
#An array object is a one-dimensional collection of objects arranged
#sequentially. Unlike arrays in many other computer languages, PDF 
#arrays may be heterogeneous; that is, an array's elements may be 
#any combination of numbers, strings, dictionaries, or any other 
#objects, including other arrays. An array may have zero elements.

def p_array(p):
    ''' array : LEFT_SQUARE_BRACKET object_list RIGHT_SQUARE_BRACKET '''
    p[0] = create_node('array',p.lexspan(0), None, p[2])

def p_object_list(p):
    ''' object_list : object object_list '''
    p[0] = [p[1]] + p[2]

def p_object_list_empty(p):
    ''' object_list : '''
    p[0] = []

#Objects
def p_object_name(p):
    ''' object : NAME '''
    p[0] = create_node('name',p.lexspan(1),p[1])                    

def p_object_string(p):
    ''' object : STRING '''                    
    p[0] = create_node('string',p.lexspan(1),p[1])

def p_object_hexstring(p):
    ''' object : HEXSTRING '''                    
    p[0] = create_node('string',p.lexspan(1),p[1])
    
def p_object_number(p):
    ''' object : NUMBER '''
    p[0] = create_node('number',p.lexspan(1),p[1])

def p_object_true(p):
    ''' object : TRUE '''                    
    p[0] = create_node('bool',p.lexspan(1),True)

def p_object_false(p):
    ''' object : FALSE '''                    
    p[0] = create_node('bool',p.lexspan(1),False)

def p_object_null(p):
    ''' object : NULL '''                    
    p[0] = create_node('null',p.lexspan(1),'null')
    
def p_object_ref(p):
    ''' object : R '''                    
    p[0] = create_node('R',p.lexspan(1),p[1])

#complex objexts
def p_object_dictionary(p):
    ''' object : dictionary '''
    p[0] = p[1]

def p_object_array(p):
    ''' object : array '''
    p[0] = p[1]
    
#7.3.7      Dictionary Objects
#A dictionary object is an associative table containing pairs of objects, 
#known as the dictionary's entries. The first element of each entry is the
#key and the second element is the value. The key shall be a name. The 
#value may be any kind of object, including another dictionary. A dictionary
#may have zero entries.
def p_dictionary(p):
    ''' dictionary : DOUBLE_LESS_THAN_SIGN dictionary_entry_list DOUBLE_GREATER_THAN_SIGN '''
    p[0] = create_node('dictionary',p.lexspan(0), None, p[2])
    
def p_dictionary_entry_list(p):
    ''' dictionary_entry_list : dictionary_entry_list NAME object
                              |  '''
    if len(p) == 1:
        p[0]=[]
    else:
        name_node = create_node('name',p.lexspan(2),p[2])
        dictionary_span = (p.lexspan(1)[0],p.lexspan(2)[1])
        dictionary_node = create_node('dictionary_entry', dictionary_span, None, [name_node,p[3]])
        p[0] = p[1] + [dictionary_node]

#7.3.10 Indirect Objects
#The definition of an indirect object in a PDF file shall consist of its 
#object number and generation number (separated by white space), followed
#by the value of the object bracketed between the keywords obj and endobj.
#EXAMPLE 1       Indirect object definition
#                12 0 obj
#                    ( Brillig )
#                endobj
def p_indirect(p):
    ''' indirect : indirect_object_stream
                 | indirect_object '''
    p[0] = p[1]


def p_indirect_object(p):
    ''' indirect_object : OBJ object ENDOBJ '''
    p[0] = create_node('indirect_object',p.lexspan(0),p[1], [p[2]])
    
def p_indirect_object_stream(p):
    ''' indirect_object_stream : OBJ dictionary STREAM_DATA ENDOBJ '''
    span = (p.lexspan(3)[0],p.lexspan(4)[0])
    stream = create_node('stream_data',span,p[3],[])
    p[0] =  create_node('indirect_object_stream',p.lexspan(0), p[1] , [p[2], stream])

#pdf
#7.5    File Structure
#A basic conforming PDF file shall be constructed of following four elements:
# [-] A one-line header identifying the version of the PDF specification 
#     to which the file conforms
# [-] A body containing the objects that make up the document contained 
#     in the file
# [-] A cross-reference table containing information about the indirect 
#     objects in the file
# [-] A trailer giving the location of the cross-reference table and of 
#     certain special objects within the body of the file
def p_xref_common(p):
    ''' xref : XREF TRAILER dictionary '''
    p[0] = create_node('xref',p.lexspan(0), p[1], [p[3]])

# 7.5.8.1:: Therefore, with the exception of the startxref address %%EOF
# segment and comments, a file may be entirely a sequence of objects.
def p_xref_stream(p):
    ''' xref : indirect_object_stream '''
    p[0] =  p[1]

#PDF_UPDATE_LIST
def p_pdf_update(p):
    ''' pdf_update : body xref pdf_end '''
    start = 0 
    if len(p[1])>0:
        start = int(p[1][0].get('lexstart'))
    else:
        start = int(p[2].get('lexstart'))
    end = int(p[3].get('lexend'))
    p[0] = create_node('pdf_update', (start,end),None,p[1]+[p[2],p[3]])

#PDF_UPDATE_LIST
def p_pdf_end(p):
    ''' pdf_end : STARTXREF EOF'''
    p[0] = create_node('pdf_end', p.lexspan(0), p[1],[])

def p_pdf_update_list(p):    
    ''' pdf_update_list : pdf_update_list pdf_update '''
    p[1].append(p[2])
    #expand(p[1],p.lexspan(0))
    p[0] = p[1]

def p_pdf_update_list_one(p):    
    ''' pdf_update_list : pdf_update '''
    p[0] = [p[1]]
    #create_node('pdf_update_list', p.lexspan(0), None, [p[1]])
    
def p_body_object(p):
    ''' body : body indirect_object 
             | body indirect_object_stream '''
    p[1].append(p[2])
#   expand(p[1],p.lexspan(0))
    p[0] = p[1]
    
def p_body_void(p):
    ''' body : '''
    p[0] = []
#    p[0] = create_node('body',p.lexspan(0),None, [])

#start = 'pdf'
def p_error(p):
    if not p:
        logger.error("EOF reached!")
    else:
        logger.error("Syntax error at [%d:%d] %s %s"%(p.lexpos,p.endlexpos, p.value,p.type))

#Used in BRUTE parsing
def p_pdf_brute_end(p):
    ''' pdf_brute_end : XREF TRAILER  dictionary STARTXREF EOF'''
    xref = create_node('xref',(0,p.lexspan(4)[0]-1), p[1], [p[3]])
    pdf_end = create_node('pdf_end', (p.lexspan(4)[0],p.lexspan(0)[1]), p[4],[])
    p[0] = [xref, pdf_end] 


# Build the parsers
parsers = {}              
for tag in ['pdf','object', 'indirect', 'pdf_brute_end']:
    logger.info("Building parsing table for tag %s"%tag)
    start = tag
    parsers[tag] = yacc.yacc(start=tag, errorlog=yacc.NullLogger())

#entry function to parse a whole pdf or portion of it..
def parse(tag,stream):
    logger.debug("Parsing a %s"%tag)
    return parsers[tag].parse(stream,tracking=True)

def normalParser(pdf):
    '''
        This will try to apply the grammar described here 
        http://feliam.wordpress.com/2010/08/22/pdf-sequential-parsing/

        Assuming endstreams are no appearing inside streams 
        we can apply an eager parser and do not Need the xref
    '''
    ret = None
    try:
        xml_element = parse('pdf',pdf)
        ret = xml_element!=None and etree.ElementTree(xml_element) or None
    except Exception,e:
        logger.error("Error in Normal parsing... %s"%e)
    return ret



def bruteParser(pdf):
    '''
        This will try to parse any object in the file based on obj/endobj and few other kewords.
        This is an ad-hoc parsing wich will try to read the file in any posile way. 
        It may produce phantom overlaped XML objects. Yo may check this issues afterwards.
        Also it is slow.
    '''
    try:
        #Search for the PDF header
        headers = list(re.finditer(r'%PDF-1\.[0-7]',pdf))
        xml_headers = []
        for header in headers:
            start = header.start()
            end = header.end()
            version = header.group(0)[-3:]
            xml_headers.append(create_node('header', (start,end), version))
        logger.info('Found %d headers'%len(xml_headers))
        
        #Search the startxref. And xrefs.
        startxrefs = list(re.finditer(r'startxref[\x20\r\n\t\x0c\x00]+[0-9]+[\x20\r\n\t\x0c\x00]+%%EOF',pdf))
        xrefs = list(re.finditer(r'xref',pdf))    
        xml_xrefs = []
        xml_pdf_ends = []
        for xref in xrefs:
            start = xref.start()
            for end in [x.end() for x in startxrefs if x.start()>xref.end()]:
                logger.info("Searching for a xref, trailer and %%%%EOF at [%s:%s]"%(start,end))
                potential_xref = pdf[start:end]
                try:
                    xml_xref, xml_pdf_end = parse('pdf_brute_end', potential_xref)
                    #fix lexspan and append
                    xml_xref.set('lexstart', str(int(xml_xref.get('lexstart'))+start))
                    xml_xref.set('lexend', str(int(xml_xref.get('lexend'))+start))
                    xml_xrefs.append(xml_xref)

                    #fix lexspan and append
                    xml_pdf_end.set('lexstart', str(int(xml_pdf_end.get('lexstart'))+start))
                    xml_pdf_end.set('lexend', str(int(xml_pdf_end.get('lexend'))+start))
                    xml_pdf_ends.append(xml_pdf_end)
                except Exception:
                    logger.info("Couldn't parse a xref, trailer and %%%%EOF at [%s:%s]"%(start,end))

        #use the force
        #This algorithm will try to match any obj with any endobj and will keep it 
        #if a sane object is found inside. Overlapping is possible here, you may analize it
        #cut it off from the xml later, using the lexspan markers.
        delimiter = r"[()<>\[\]/%\x20\r\n\t\x0c\x00]"
        objs = list(re.finditer(r'\d+\x20\d+\x20obj'+delimiter, pdf))
        endobjs = list(re.finditer(delimiter+r'endobj', pdf))
        streams = list(re.finditer(delimiter+'stream'+delimiter, pdf))
        endstreams = list(re.finditer('endstream'+delimiter+'endobj', pdf))
        xml_iobjects = []
        logger.info("Found %d Object starting points"%len(objs))
        logger.info("Found %d Object ending points"%len(endobjs))
        for m in objs:
            start = m.start()
            for end in [x.end() for x in endobjs if x.start()>m.end()]:
                try:
                    logger.debug("Parsing potential object at [%s:%s]"%(start,end))
                    potential_obj = pdf[start:end]
                    escape_endstreams = [e.start()+start for e in endstreams if e.start()>start and e.end()<end ]

                    for e in escape_endstreams[:-1]:
                        potential_obj = potential_obj[:e] +"X"*9 + potential_obj[e+9:]

                    xml_iobject = parse('indirect',potential_obj)
                    if xml_iobject == None:
                        continue
                    #fix lexspan
                    xml_iobject.set('lexstart', str(int(xml_iobject.get('lexstart'))+start))
                    xml_iobject.set('lexend', str(int(xml_iobject.get('lexend'))+start))
                    #FIX: fix escape
                    #WRONG offset!!!!!!!!!!!!
                    pl = payload(xml_iobject)
                    for e in escape_endstreams[:-1]:
                        pl = pl[:e] +"endstream" + pl[e+9:]
                    setpayload(xml_iobject, pl)
                    #append to the list
                    xml_iobjects.append(xml_iobject)
                    #Just parse the first object we can of this try.
                    break
                except Exception,e:
                    logger.error("Received exception %s"%e)
                    logger.debug("Could not parse potential object at [%s:%s]."%(start,end))
        logger.info("Succesfully parsed %d/%d Objects ending points"%(len(xml_iobjects),len(endobjs)*len(objs)))

        #summ all the objects
        allobjects = xml_headers + xml_xrefs + xml_pdf_ends + xml_iobjects

        if len(xml_headers) == 0:
            logger.info("%%%%EOF tag was not found! Creating a dummy.")
            allobjects.append(create_node('pdf_end', (len(pdf),len(pdf)), "-1"))

        if len(xml_headers) == 0:
            logger.info("%%%%PDF-N-M tag was not found! Creating a dummy.")
            allobjects.append(create_node('header', (0,len(pdf)), "NOVERSION",[] ))

        #Sort it as they appear in the file
        allobjects = sorted(allobjects,lambda x,y: cmp(int(x.get('lexstart')), int(y.get('lexstart'))))

        #recreate XML structure 'best' we can...
        assert allobjects[0].tag == 'header'
        root_element = create_node('pdf', (0,len(pdf)), "OPAF!(raw)",[allobjects.pop(0)])
        
        update = create_node('pdf_update',(0,0))
        while len(allobjects)>0:
            thing = allobjects.pop(0)
            update.append(thing)
            if thing.tag == 'pdf_end':
                root_element.append(update)
                update = create_node('pdf_update',(0,0))
        if len(update)>0:
            logger.info("Missing ending %%EOF")
            root_element.append(update)

        return etree.ElementTree(root_element)
    except Exception,e:
        logger.error("Brute-Parsing a %s"%tag)    
    return None

def xrefParser(pdf):
    '''
        This will try to parse the pdf based on the tree of cross references.
        Hard, uninmplemented and insane.
    '''
    assert False, "Uninmplemented!"
    if False:                
        try:
            xrefpos = int(pdf[startxrefpos+9:])     
        except:
            logger.info("Damn! Startxref is broken! Lower chances of parsing this..")
            #Idea: look for lowest xref/Root an try there
            #If not try obj/endobj
            assert False, "Unimplemented"
        if pdf[xrefpos].isnum() :
            logger("Main cross reference is a XrefStream")
            assert False, "Unimplemented"
        elif pdf[xrefpos:xrefpos+5] == "xref" :
            logger("Main cross reference is a NoRMAL xref")
            assert False, "uninmplemented"                                    
        else:
            logger("XREF not found. Is this a pdf? Where did you get this?")
            assert False, "uninmplemented"                    
    #cri cri...

def multiParser(pdf):
    ''' 
        Try the different parsing strategies in some preference order...
    '''
    #fallback chain of different type of parsing algorithms
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
    return xml_pdf
    
if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except:
        pass

    if False:
        print "Test parse isolated objects"        

        print parse('object', "[ 1 (string) <414141> null ]")
        print parse('object', "1")
        print parse('object', "(string)")
        print parse('object', "<41414141>")
        print parse('object', "<< /entry1 1 /entry2 (string) /entry3 <414141> /entry4 null >>")
        print parse('indirect', "1 0 obj\n1\nendobj")
        print parse('indirect', "1 0 obj\n(string)\nendobj")
        print parse('indirect', "1 0 obj\n<41414141>\nendobj")
        print parse('indirect', "1 0 obj\n[1 (string) <414141> null]\nendobj")
        print parse('indirect', "1 0 obj\n<</key 1>>\nendobj\n2 0 obj\n<</key 2\nendobj") #TODO: test/fix It should return error(Its not just 1 object)
        
    bytes = 0
    files = 0
    for filename in sys.argv[1:] :
        print filename
        try:
            s = file(filename,"r").read()
            files += 1
            bytes += len(s)
            try:
                result = parse('pdf',s)
            except:
                result = bruteParse(s)
            print(etree.tostring(result, pretty_print=True))

        except Exception,e:
            print "OH", e

