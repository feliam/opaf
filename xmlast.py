from lxml import etree
import math

#Logging facility
import logging
#logging.basicConfig(filename='opaf.log',level=logging.DEBUG)
logger = logging.getLogger("OPAFXML")

#Used to set/get and use the base64 encoding inse and out xpath
ns = etree.FunctionNamespace(None)

codec = 'base64'
ns['dec'] = lambda dummy, s: s[0].decode(codec)
ns['enc'] = lambda dummy, s: s.encode(codec)

        
def payload(e):
    return e.get('payload').decode(codec)

def setpayload(e,s):
    e.set('payload',s.encode(codec))

from lxml import etree
#auxiliary function for confortably create a XML Element
def create_node(tag,lexspan,pld="",children=[]):
    xml = etree.Element(tag, lexstart=str(lexspan[0]),lexend=str(lexspan[1]))
    setpayload(xml,str(pld))
    for c in children:
        xml.append(c)
    return xml


#auxiliary function to expand the lexspan (where it starts/ends)
def expand_span(e,span):
        begin,end = int(e.get('lexstart')), int(e.get('lexend'))
        e.set('lexstart', str(min(begin,span[0])))
        
        if abs(end - max(end,span[1])) >100:
            print "EPAA!!!", e.tag
        e.set('lexend', str(max(end,span[1])))

def xmlToPy(e,paths={}):
    '''
        This traslate a xml-pdf direct object into its python version.
        I will copy things and changes will not be propagated.
    '''
    if e.tag in ['name','string']:
        return payload(e)
    elif e.tag == 'number':
        f = float(payload(e))
        if (math.floor(f) == f):
            return int(f)
        else:
            return f
    elif e.tag == 'bool':
        return {'True':True,'False':False}[payload(e)]
    elif e.tag == 'null':
        return None
    elif e.tag == 'R':
        if not e.get('path'):
            return None
        path = e.get('path')
        if path in paths.keys():
            logger.debug("xmlToPy already processed R %s path:%s"%(payload(e),e.get('path')))
            return [paths[path]]
        logger.debug("xmlToPy diving into R %s  path:%s"%(payload(e),e.get('path')))
        paths[path] = []
        paths[path].append(xmlToPy(e.xpath(path)[0][0],paths))
        return paths[path]
    elif e.tag == 'dictionary_entry':
        assert e[0].tag == 'name', 'First dictionary entry child yould be a name'
        return (payload(e[0]), xmlToPy(e[1],paths))
    elif e.tag == 'dictionary':
        entries = dict([xmlToPy(c,paths) for c in e])
        assert len(entries) == len(e), 'Number of entries py and xml dictionary should match ' 
        return dict(entries)
    elif e.tag == 'array':
        return [xmlToPy(c,paths) for c in e]
    assert False, logger.error("It didn't make it to its python form...%s",e)


