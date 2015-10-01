#opaf.py usage

# Usage #

OPAF if used to analyze potentially malicious PDFs.
```
cat malware.pdf | python opaf.py -d >malware.xml
```

```
opaf $ python opaf.py --help
Usage: opaf.py [options]

Options:
  -h, --help            show this help message and exit
  -x XML, --xmlfile=XML
                        Generate an xml file.
  -l LOG, --logfile=LOG
                        Dump log messages to LOG file.
  -i, --interactive     Throw interactive python shell
  -g GRAPH, --graph=GRAPH
                        Generate and dump graph to GRAPH.
  -d, --decompress      Apply a filter pack to decompress and parse objec
                        streams.
```