
#Logging facility
import logging
#logging.basicConfig(filename='opaf.log',level=logging.DEBUG)
logger = logging.getLogger("OPAFLib")


from parser import parse,bruteParser,normalParser,xrefParser
from xmlast import payload,setpayload,xmlToPy,etree


from filters import defilterData
from xref import *

def expand(e):
    '''
        This will expand an indirect_object_stream and modify it in place
        It may delete the Filter, DecodeParams, JBIG2Globals keywords of 
        the dictionary
    '''
    dictionary_py = xmlToPy(e[0])
    if not 'Filter' in dictionary_py.keys():
        logger.info( 'A filteres/compressed stream shall have the Filter key. obj %s already expanded?',payload(e))
        return True
    filters = dictionary_py['Filter']
    params = dictionary_py.get('DecodeParms',None)
    assert any([type(filters) == list and (type(params) == list or params==None ),
                type(filters) != list and (type(params) == dict or params==None ) ]), 'Filter/DecodeParms wrong type'

    if type(filters) != list:
        filters=[filters]
        params=params and [params] or [{}]

    if params == None:
        params = [{}]*len(filters)
        
    assert all([type(x)==str for x in filters]), 'Filter shall be a names'
    assert all([type(x)==dict for x in params]), 'Params shoulb be a dictionary.. or null?'
    assert len(filters) == len(params),'Number of Decodeparams should match Filters'
    if len(set(['DCTDecode','CCITTFaxDecode','JPXDecode','JBIG2Decode']).intersection(set(filters)))>0:
        return False
    #Expand/defilter data
    data = payload(e[1])
    try:
        for filtername,param in reversed(zip(filters,params)):
            data = defilterData(filtername,data, param)
        setpayload(e[1],data)   

        #remove /Filter and /DecodeParms from stream dictionary
        for rem in e[0].xpath('./dictionary_entry/*[position()=1 and @payload=enc("Filter") or @payload=enc("DecodeParms")]/..'):
            e[0].remove(rem)

        return True
    except Exception,ex:
        logger.error('Error defiltering data with %s(%s). Exception: %s. Saving error stream on %s.error'%(filtername, params, ex, filtername))
        file('%s.error'%filtername,'w').write(data)
    return False

def expandObjStm(xml_pdf,iostream):
    '''
        This parses the ObjStm structure and add all the new indirect
        objects ass childs of the ObjStm node.
    '''
    dictionary = xmlToPy(iostream[0])
    assert not 'Filter' in dictionary.keys(), "ObjStm should not be compressed at this point"
    assert 'N' in dictionary.keys(), "N is mandatory in ObjStm dictionary"
    assert 'First' in dictionary.keys(), "First is mandatory in ObjStm dictionary"
    assert len(iostream) == 2, "It is already expanded, or SITW!"
    data = payload(iostream[1])
    pointers =  [int(x) for x in data[:dictionary["First"]].split()]
    assert len(pointers)%2 == 0 , "Wrong number of integer in the ObjStm begining"
    pointers = dict([(pointers[i+1]+dictionary["First"],pointers[i]) for i in range(0,len(pointers),2) ])
    positions = pointers.keys()
    positions.sort()
    positions.append(len(data))
    object_stream = etree.Element('object_stream', lexstart=iostream[1].get('lexstart'),
                                                   lexend=iostream[1].get('lexend'), 
                                                   payload="")
    iobjects = xml_pdf.xpath('//*[starts-with(local-name(),"indirect_object")]')

    for p in range(0,len(positions)-1):
        logger.info("Adding new object %s from objectstream %s"%((pointers[positions[p]],0),payload(iostream)))
        begin,end = (positions[p], positions[p+1])
        xmlobject = parse('object', data[positions[p]:positions[p+1]]+" ")
        io = etree.Element('indirect_object', lexstart=iostream[1].get('lexstart'),
                                              lexend=iostream[1].get('lexend'))
        setpayload(io,repr((pointers[positions[p]],0)))
            
        io.append(xmlobject)
        object_stream.append(io)
    iostream.append(object_stream)
    
    iobjects = xml_pdf.xpath('//*[starts-with(local-name(),"indirect_object")]')


def getStartxref(xml_pdf):
    '''
       Get the last startxref pointer (should be at least one)
    '''
    startxref = xml_pdf.xpath('/pdf/pdf_update/pdf_end')
    assert len(startxref)>0, 'PDF file should have at least one startxref marker'
    return int(payload(startxref[-1]))

def getMainXref(xml_pdf,startxref=None):
    '''
        Get the Trailer dictionary (should be at least one)
    '''
    if startxref == None:
        startxref = getStartxref(xml_pdf)
    xref = xml_pdf.xpath('//*[@lexstart="%s" and (local-name()="xref" or local-name()="indirect_object_stream")]'%startxref )
    assert len(xref) == 1, 'PDF file should have one Main xref'
    #trailer may be normal xref o xrefstream
    assert xref[0].tag in ['indirect_object_stream', 'xref'], 'The trailer/xref should be correct'
    return xref[0]

def getRoot(xml_pdf, xref=None, startxref=None):
    '''
        Get the pdf Root node.
    '''
    if xref == None:
        xref = getMainXref(xml_pdf, startxref)
    #Get the root reference
    root_ref = xref.xpath('.//dictionary/dictionary_entry/name[position()=1 and fromb64(@payload)="Root"]/../R')
    assert len(root_ref) == 1, 'Trailer should point to one Root'
    root_ref = payload(root_ref[0])

    #Get the Root
    root = xml_pdf.xpath('//indirect_object[fromb64(@payload)="%s"]'%root_ref)            
    assert len(root) == 1, 'Should be only one Indirect %s object.'%root_ref
    return root[0]

def getIndirectObjectsDict(xml_pdf):
    '''
        List of indirect objects.
        Return a dictionary with this look: 
                 { '(10, 0)' :  '<indirect_object ... ></indirect_object>', ...}
    '''
    iobjects = xml_pdf.xpath('//*[starts-with(local-name(),"indirect_object")]')
    return dict([(payload(x),x) for x in iobjects])

def getIndirectObject(xml_pdf, ref):
    '''
        Find an indirect object referenced by ref.
        ref should be a string like "(10, 0)" or the actual pair of ints.
        Returns none if not found.
    '''    
    iobject = xml_pdf.xpath('//*[ starts-with(local-name(),"indirect_object") and @payload=enc("%s")]'%ref) 
    assert len(iobject) <= 1, "More than an indirect object with the same id: %s"%payload(ref)
    logger.debug("Searching for %s indirect object. %s"%(ref, len(iobject)==1 and "Found" or "Not Found!!"))
    return (iobject+[None])[0]


def canonizeNames(xml_pdf, traslate=None):
    '''
        Search the tree for keywords in dictionaries and traslate 
        then to canonized form or to any ad-hoc traslation you pass
        in the dictionary { string -> string } you pass.
    '''
    if not traslate:
        traslate = { 'Fl': 'Filter',
                     'DP': 'DecodeParams',
                     }
    keywords = xml_pdf.xpath('//dictionary_entry/name[position()=1]')
    print "Canonize!",[str(payload(x)) for x in keywords]

def getUnresolvedRefs(xml_pdf):
    '''
        List Unresolved References
    '''
    return xml_pdf.xpath('//R[not(@path)]')
    
    
def resolvRef(xml_pdf, xml_ref, iobjects=None):
    '''
        Mark a reference as resolved. It adds a @path attribute to the R node.
        @path points to the indirect object the reference resolves to.
        It expects iobject to be a map of references to indirect_objects paths.
        If iobjects is None resolvRef search the whole xml for it.
    '''
    iobject = None
    ref = payload(xml_ref)
    #finde the iobject
    if iobjects!=None and ref in iobjects.keys():
        logger.debug("Searching for %s indirect object in iobject dict"%(ref))
        
        iobject = iobjects[ref]
    else:
        logger.debug("Searching for %s indirect object in xml"%ref)
        iobject = getIndirectObject(xml_pdf, ref)

    #Fix the reference (R)
    if iobject != None:
        logger.debug("IObject %s found.."%payload(iobject))
        xml_ref.set('path',xml_pdf.getpath(iobject))
    else:
        logger.debug("IObject %s NOT found.."%ref)
        if 'path' in xml_ref.attrib.keys():
            del(xml_ref.attrib['path'])

def getFilteredStreams(xml_pdf):
    '''
        List of compresed/filtered indirect streams in xml_pds
    '''
    return xml_pdf.xpath('//indirect_object_stream/dictionary/dictionary_entry/name[@payload=enc("Filter")]/../../.. ')

def getStreamsOfType(xml_pdf, ty):
    '''
        Find all streams of Type ty in xml_pdf.
        For ex.  getStreamsOfType(xml_pdf, 'ObjStm')
    '''
    return xml_pdf.xpath('//indirect_object_stream/dictionary/dictionary_entry/name[@payload=enc("Type")]/../*[position()=2 and @payload=enc("%s")]/../../.. '%ty)

def getTypeOfStream(xml_pdf):
    '''
        Returns ty Type of the stream in xml_pdf.
    '''
    ty = xml_pdf.xpath('//indirect_object_stream/dictionary/dictionary_entry/name[@payload=enc("Type")]/../*[position()=2]')
    return len(ty)==0 and None or ty[0]


def doEverything(xml_pdf):
    '''
        This script will try to expand, parse an fix references for every iobject 
    '''
    #Canonize names
    logger.info("Canonizing key names")
    canonizeNames(xml_pdf)

    #List of indirect objects.
    logger.info("Updating list of reacheable indirect objects")
    iobjects = getIndirectObjectsDict(xml_pdf)

    #Try to resolv all references now
    logger.info("Solving unsolved references")            
    for ref in getUnresolvedRefs(xml_pdf):
        resolvRef(xml_pdf, ref, iobjects)
                
    #List all filtered Streams
    logger.info("Expand all compressed streams")
    istreams = getFilteredStreams(xml_pdf)
    #Expand every compresed stream
    #this will replace the node with the expanded version
    for istream in istreams:
        expand(istream)

    #List of Objectstreams streams
    logger.info("Parse and asimilate all ObjStms (compresed objects)")
    iobjstreams = getStreamsOfType(xml_pdf, 'ObjStm')            
    logger.info("There are %d ObjStm"%len(iobjstreams))

    iobjects = xml_pdf.xpath('//*[starts-with(local-name(),"indirect_object")]')

    for iostream in iobjstreams:
        expandObjStm(xml_pdf,iostream)


    #List of indirect objects.
    logger.info("Updating list of reacheable indirect objects after expanding ObjStm")
    iobjects = getIndirectObjectsDict(xml_pdf)

    #Try to resolv all references now
    logger.info("Solving unsolved references")            
    for ref in getUnresolvedRefs(xml_pdf):
        resolvRef(xml_pdf, ref, iobjects=iobjects)

    #Check reference consistency
    urefs = getUnresolvedRefs(xml_pdf)
    if len(urefs)!= 0:
        logger.info("It should not be broken references at this point.%s"%[payload(r) for r in urefs])


####
#### GRAPH
####
def graph(xml_pdf,png=None):
    import matplotlib.pyplot
    import networkx as nx
    import matplotlib.pyplot as plt
    try:
        from networkx import graphviz_layout
    except ImportError:
        raise ImportError("This example needs Graphviz and either PyGraphviz or Pydot")


    G=nx.DiGraph()
    iobjects = getIndirectObjectsDict(xml_pdf)
    for x in iobjects.keys():
        G.add_node(x)
        for r in iobjects[x].xpath(".//R"):
            G.add_edge(x,payload(r))            

    try:
        root = getRoot(xml_pdf)
        G.add_edge("trailer",payload(root))            
    except Exception,e :
        G.add_node("trailer")            
        pass

    pos=nx.graphviz_layout(G,prog='neato',args='')
    plt.figure(figsize=(8,8))
    nx.draw(G,pos,node_size=20,alpha=0.5,node_color="blue", with_labels=False)
    plt.axis('equal')
    if png :
        plt.savefig(png)
    else:
        plt.show()

def getXML(xml_pdf):
    ''' 
        Returns a string containing the prettyprinted XML of the pdf.
    '''
    from copy import deepcopy
    logger.info("Generating XML output")
    output_xml = deepcopy(xml_pdf)
    #HACK to make it more humanly readeable.
    for e in output_xml.xpath('//*'):
        try:
            p = payload(e)
            if p == "None":
                del(e.attrib['payload'])
            elif set(map(chr, range(0,10) + range(11,32) + range(127,160))).isdisjoint(p):
                e.set('payload',p)
        except Exception,ex:
            logger.error("Exception generating the XML (%s)"%ex)

    return etree.tostring(output_xml,  pretty_print=True)
    


