import os, sys
import xml.etree.ElementTree as tree
import urllib2
from urllib import urlencode
import random
import time as t
from optparse import OptionParser
import datetime
import hashlib

###############
# Setting up the options the user can set.
# -w is the max time the service have to respond before a warning is given
# -c is the max time the service have to respond before a critical warning is given
# -t is the max time the service have to respond.
# -n is the number of layers to test with
# --cached is a flag. If the flag is set, the script will only use getCap one time a day
###############

parser = OptionParser()

parser.add_option(  "-w", 
                    dest = "warning", 
                    default = 10000, 
                    type = "int",
                    help = "The maximum time, accepted for the service to run normally"
                    )
parser.add_option(  "-c", 
                    dest = "critical",
                    default = 30000,
                    type = "int",
                    help = "The threshold for the test, if the service doesn't respon by this time \
                            it's considered to be down"
                    )
parser.add_option(  "-t",
                    dest = "timeout",
                    default = None,
                    type = "int",
                    help = "set the timeout timer (default is 30 sec.)"
                    )
parser.add_option(  "-n",
                    dest = "layerCount",
                    default = None,
                    type = "int",
                    help = "The numbers of layers to be checked (defualt is all of them)"
                    )
parser.add_option(  "--cached", 
                    dest = "cached", 
                    action="store_true",
                    help = "")
parser.add_option(  "-l", 
                    dest = "listLayer", 
                    action="store_true",
                    help = "Get list all the tested layers (This should not be used with nagios)")
parser.add_option(  "-g", 
                    dest = "getGeo", 
                    action="store_true",
                    help = "")
parser.add_option(  "-s", 
                    dest = "speLayer", 
                    type = "string", 
                    help = "specify layers to test (if multiple layers seperate with a ',')")
                    

                    
(options, args) = parser.parse_args()

def check_wms(options, urls):
    """
    Checks a wms service with options and url given
    
    The following is an example on how to run the script:
    
        > python check_wms.py http://kort.arealinfo.dk/wms?servicename=landsdaekkende_wms -n 10 --cached -t 30
        > Everything if O.K
        
    In this example the test service is http://kort.arealinfo.dk/wms?servicename=landsdaekkende_wms.
    We only wanted to test 10 layers and the timeout is set to 20 sec
    and we want the capabilitis to be cached.
    
    @rtype: int
    @return: Returns a nagios return code
    """
    # Get the options set by the user
    url, args = packUrl(urls[0])
    
    layerCount = options.layerCount
    if options.timeout is not None:
        tout = (options.timeout / 1000)
    else:
        tout = options.timeout
    critTimer = options.critical
    warnTimer = options.warning
    
    listLayers = options.listLayer
    getGeo = options.getGeo
    
    flag = options.cached
    
    
    try:
        wms = WebMapService(url, args, flag, timeout = tout)
    except urllib2.URLError, e:
        raise e
        print "Get Capability got a timeout"
        return 2
    
    rOptions = wms.getRandomData(layerCount)
    
    if options.speLayer is not None:
        speLayers = options.speLayer.split(',')
        layers = []
        wmsLayers = wms.getLayersDict()
        for lName in speLayers:
            if lName in wmsLayers:
                layers.append((lName, wmsLayers[lName].getRandomBbox(rOptions["SRS"])))
    else:
        layers = rOptions["Layers"]
    
    #Runtime container
    timeDict = {}
    startTime = t.time()
    time = 0
    # Start to test the layers
    for layer in layers:
        try:
            if listLayers is not None:
                print layer[0]
            t0 = t.time()
            check_service(wms, layer[0], "default", rOptions["SRS"], layer[1], rOptions["Format"])
            t1 = t.time()
            time = t1 - t0
            time*= 1000
            # print "%s was %d before being done" % (layer[0], time)

            result = 0

            # Check what the result should be.
            if warnTimer <= time < critTimer:
                result = 1
            elif critTimer <= time < tout:
                result = 2
        except urllib2.URLError, e:
            result = 2
            raise e
       
            
        if result not in timeDict:
            timeDict[result] = []
            
        data = (layer[0], layer[1], time)
        timeDict[result].append(data)
        
    endTime = t.time()
    capTime = (endTime - startTime) * 1000
    # print "it took %f ms" % capTime

    endData = packData(timeDict, capTime, getGeo)
        
    keys = timeDict.keys()
    
    keys.sort()
    
    maximum = keys.pop()
    
    if maximum is 2:
        endStr = "there is %d layers, which is critical" % len(timeDict[maximum])
        print "%s|%s" % (endStr, endData)
        return 2
    elif maximum is 1:
        endStr = "There is %d layers, which is warrning" % len(timeDict[maximum])
        print "%s|%s" % (endStr, endData)
        return 1
    else:
        endStr = "Everything is O.K"
        print "%s|%s" % (endStr, endData)
        return 0

def packUrl(urlStr):
    """docstring for packUrl"""
    url = urlStr.split('?')[0]
    
    argDict = {}
    
    if len(urlStr.split('?')) > 1:
        arg = urlStr.split('?')[1]
        for argtup in arg.split('&'):
            key, value = argtup.split('=')
            argDict[key] = value
        
    if not "version" in argDict:
        argDict["version"] = "1.1.1"
        
    if not "service" in argDict:
        argDict["service"] = "WMS"
        
    return url, argDict

def packData(values, capTime, getGeo):
    """docstring for packData"""
    timeList = []
    resStr = ""
    for key in values:
        for value in values[key]:
            name = value[0]
            bbox = value[1]
            time = value[2]
        
            timeList.append(time)
            if key is 2:
                nStr = "'t_%s'=%dms;%s" % (name, time, "crit")
            elif key is 1:
                nStr = "'t_%s'=%dms;%s" % (name, time, "warn")
            else:
                nStr = "'t_%s'=%dms" % (name, time)
                
            if getGeo is not None:
                xStr = "'x_%s'=%d" % (name, (float(bbox[0]) + 50))
                yStr = "'y_%s'=%d" % (name, (float(bbox[1]) + 50))
                resStr += ",%s,%s,%s" % (nStr, xStr, yStr)
            else:
                resStr += ",%s" % (nStr)
        
    timeList.sort()
    
    minStr = ",'t_min'=%dms" % timeList[0]
    maxStr = ",'t_max'=%dms" % timeList.pop()
    oStr = "'t_get_capabilities'=%d" % capTime
    
    return oStr + maxStr + minStr + resStr


def check_service(wms, layer, style, srs, bbox, format, size = (200,200)):
    """docstring for check_service"""
    img = wms.getMap( layer = layer,
                    style = style,
                    srs = srs,
                    bbox = bbox,
                    size = size,
                    format = format
                    )

class WebMapService():
    """docstring for WebMapService"""
    def __init__(self, url, urlArgs, flag, timeout = None):
        self.url = url
        self.urlArgs = urlArgs
        self.version = urlArgs['version']
        self.flag = flag
        self.formats = []
        self.boundingbox = {}
        self.timeout = timeout
        self.layers = []
        self.operation = {}
        self.newXml()
        self.getCapability()

    def getCapability(self):
        # Format url
        # urlsplits = self.url.split('&')
        #        urlBase = urlsplits[0] + "&version=" + self.version \
        #              + "&service=wms&REQUEST=GetCapabilities"
        #        
        #        # Open the url
        #        f = urllib2.urlopen(urlBase, timeout = self.timeout)
        
        etree = tree.parse(self.fName)
        root = etree.getroot()

        capability = root.find("Capability")

        getmap = capability.find("Request").find("GetMap")

        for format in getmap.findall("Format"):
            self.formats.append(format.text)

        get1 = getmap.find("DCPType/HTTP/Get/OnlineResource")
        self.operation["get"] = get1.attrib['{http://www.w3.org/1999/xlink}href']

        layers = capability.find("Layer")

        for srs in layers.findall("SRS"):
            self.boundingbox[srs.text] = []

        bbox = layers.findall("BoundingBox")

        for b in bbox:
            box = ( b.attrib["minx"], b.attrib["miny"] ,
                    b.attrib["maxx"], b.attrib["maxy"])
            self.boundingbox[b.attrib["SRS"]] = box

        # Get all the layers!
        layer = layers.findall("Layer")
        for lay in layer:
            name = lay.find("Name").text
            title = lay.find("Title").text
            tmpBBox = lay.findall("BoundingBox")
            if len(tmpBBox) is 0:
                bBox = self.boundingbox
            else:
                bBox = {}
                for b in tmpBBox:
                    box = ( b.attrib["minx"], b.attrib["miny"] ,
                            b.attrib["maxx"], b.attrib["maxy"])
                    bBox[b.attrib["SRS"]] = box
            l = Layer(name, title, bBox)
            self.layers.append(l)
    
    def newXml(self):
        """
        newXml determines if there will be made a new cached xml file of the capabilitis

        @param  url: The url of the service.
        @param  flag: The flag set by the user, if this flag is said there won't be created a new xml file
        @param  timeout: user specific timeout.
        @param  verison: The version for the servcie.
        @return: The filename of the xml file whether or not a new file was created.
        """
        # Get the base url and create a hash of it
        # for the filename
        realUrl = self.url
        m = hashlib.md5()
        m.update(realUrl)
        fName = str(m.hexdigest()) + ".xml"

        if self.flag:
            if not os.path.exists(fName) or not self.checkDate(fName):
                self.getCap()
        else:
            self.getCap()

        self.fName = fName


    def checkDate(self, fName):
        """
        checkData checkes if the data the xml file was created is the same
        as today

        @param  fName: The name of the file to check.
        @return: whether or not the file was created today
        """
        year = t.localtime(os.stat(fName).st_atime).tm_year
        mon = t.localtime(os.stat(fName).st_atime).tm_mon
        day = t.localtime(os.stat(fName).st_atime).tm_mday

        if datetime.date(year, mon, day) == datetime.date.today():
            return True
        else:
            return False


    def getCap(self):
        
        request = self.urlArgs
        
        if not "request" in request:
            request["request"] = "GetCapabilities"
        
        data = urlencode(request)

        xmlCap = urllib2.urlopen((self.url + "?" + data), timeout = self.timeout)

        m = hashlib.md5()
        m.update(self.url)

        fName =  str(m.hexdigest()) + ".xml"

        fp = open(fName, 'w')

        fp.write(xmlCap.read())

        fp.close()

        self.fName = fName

    def getMap( self, layer, style, srs, 
                bbox, format, size,
                bgcolor='#FFFFFF',
                exceptions='application/vnd.ogc.se_xml',
                method='Get',):
                
        urlBase = self.operation["get"]        
        request = {'version': self.version, 'request': 'GetMap'}

        request['layers'] = layer
        
        request['styles'] = style
        
        request['transparent'] = "FALSE"

        request['width'] = str(size[0])
        request['height'] = str(size[1])

        request['srs'] = str(srs)
        request['bbox'] = ','.join([repr(x) for x in bbox])
        request['format'] = str(format)
        request['bgcolor'] = '0x' + bgcolor[1:7]
        request['exceptions'] = str(exceptions)

        data = urlencode(request)

        u = urllib2.urlopen((urlBase + '?' + data), timeout = self.timeout)

        # check for service exceptions, and return
        if u.info()['Content-Type'] == 'application/vnd.ogc.se_xml':
            se_xml = u.read()
            se_tree = tree.fromstring(se_xml)
            err_message = unicode(se_tree.find('ServiceException').text).strip()
            print err_message
        return u



    def getRandomData(self, count):
        """docstring for getRandomLayers"""
        #Container
        resDict = {}

        srs = random.sample(self.boundingbox.keys(), 1)[0]
        if count is not None and count < len(self.layers):
            rLayers = random.sample(self.layers, count)
        else:
            rLayers = self.layers
            
        resDict["SRS"] = srs

        resDict["Layers"] = []

        for layer in rLayers:
            resDict["Layers"].append((layer.name, layer.getRandomBbox(srs)))

        resDict["Format"] = random.sample(self.formats, 1)[0]

        return resDict
        
    def getLayersDict(self):
        layerDict = {}
        for layer in self.layers:
            layerDict[layer.name] = layer
        return layerDict


class Layer():
    """
    The layer class keeps the information for each layer from the service
    """
    def __init__(self, name, title, srs):
        """
        @type   name: string
        @param  name: the name of the layer
        
        @type   title: string
        @param  title: The title of the layer
        
        @type   srs: dict
        @param  srs: A dictionary containing srs's and their bounding box
        
        @rtype: Layer object
        @return: A layer containing all relevant data
        """
        self.name = name
        self.title = title
        self.srs = srs

    def getRandomBbox(self, srs):
        """docstring for getRandomBbox"""
        bBox = self.srs[srs]
        scaleX = 100.0 / (float(bBox[2]) - float(bBox[0]))
        scaleY = 100.0 / (float(bBox[3]) - float(bBox[1]))
        maxX = float(bBox[2]) - scaleX
        maxY = float(bBox[3]) - scaleY

        randomX = random.uniform(float(bBox[0]), maxX)
        randomY = random.uniform(float(bBox[2]), maxY)
        
        res0 = "%.4f" % randomX
        res1 = "%.4f" % randomY
        res2 = "%.4f" % (randomX + scaleX)
        res3 = "%.4f" % (randomY + scaleY)
        
        randomBox = (res0, res1, res2, res3)

        return randomBox

check_wms(options, args)
    