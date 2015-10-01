# Parse #
First thing to do is to lift the PDF structure to XML. Thats done with somethink like this...
```
import opaflib

filename = 'input.pdf'
pdf = file(filename,"r").read()
xml_pdf = opaflib.multiParser(pdf)

```
... now you have the PDF formatted as an XML tree.

## Save it as xml ##
Before trying to explore it you shoul save it and browse it with some xml viewer as xmlcopyeditor (http://xml-copy-editor.sourceforge.net/).

```
xml_str = opaflib.getXML(xml_pdf)
file('output.xml').write(xml_str)
```

# Examples of arbitrary XPATH analysis #
Now the PDF is in XML and you may query it using XPATH. CHeck out the xpath basics here -> http://www.w3schools.com/xpath/default.asp. It is as ugly as powerful, give it a chance.

## PDF-XPATH examples ##
### All objects in the tree ###
```
xml_pdf.xpath('//') 
```

### Get all indirect objects ###
```
   '//*[starts-with(local-name(),"indirect_object")]'
```

### Check for /Javascript ###
```
   '//dictionary/dictionary_entry/name[position()=1 and dec(@payload)="Javascript"]' 
```

### Get every PDF Reference ###
```
   '//R[not(@path)]'`     
```

## XPATH from python ##

### Count all indirect objects (including streams) ###
```
print len(xml_pdf.xpath('//*[starts-with(local-name(),"indirect_object")]'))
```

### List all used Filters in the PDF ###
```
filters = xml_pdf.xpath('//dictionary_entry/name[dec(@payload)="Filter"]/../*[position()=2]/*[local-name()="name"]')
print ", ".join(list(set([opaflib.payload(x) for x in filters])))
```

# Expand all your streams before analysis #
If you want to analyse inside compressed objects (ObjStm) you can prepend  something like this..

```
opaflib.doEveryting(xml_pdf)
```

_Comments, help!, examples, help! are wellcome._