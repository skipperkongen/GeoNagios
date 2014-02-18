# About GeoNagios

GeoNagios is a plugin for the monitoring system [Nagios](http://nagios.org/). It tests the availability and performance of a geospatial web service, e.g. [Web Map Service](http://en.wikipedia.org/wiki/Web_Map_Service) (WMS). 

<table>
<tr><th>Protocol</th><th>Implemented by</th><th>Finished</th></tr>
<tr><td>WMS</td><td>check_wms.py</td><td>✓</td></tr>
<tr><td>WFS</td><td>check_wfs.py</td><td></td></tr>
<tr><td>WCS</td><td>check_wcs.py</td><td></td></tr>
<tr><td>CSW</td><td>check_csw.py</td><td></td></tr>
<tr><td>WMTS</td><td>check_wmts.py</td><td></td></tr>
<tr><td>TMS</td><td>check_tms.py</td><td></td></tr>
</table>

GeoNagios has been developed with support from the [Danish Geodata Agency](http://www.gst.dk) and the [University of Copenhagen, Department of Computer Science](http://di.ku.dk/).

## Dependencies

GeoNagios is written in [Python](http://www.python.org/) (tested with 2.6 and 2.7). Dependencies are Python 2.5+ and [pyproj](http://code.google.com/p/pyproj/). It currently only supports WMS, but additional protocols are planned.

```bash
# easy_install pyproj
pip install pyproj  # maybe need 'sudo' in front
```

## Getting Started

```bash
curl -o check_wms.py https://raw.github.com/skipperkongen/GeoNagios/master/check_wms.py
chmod u+x check_wms.py
./check_wms.py 'http://kortforsyningen.kms.dk/service?ticket=1940ecb511e4d1a92df01347a85aa30f&servicename=dagi' -l
```


New sections:

* Getting started with GeoNagios
* Install and configure Nagios (the general purpose monitoring software) to use GeoNagios
* Installing GeoNagios on EC2

Old sections

* [How GeoNagios works](docs/how-geonagios-works.md) - Description of the method used to test services
* [Installing GeoNagios on EC2](geonagios-on-ec2.md) - These instruction a for Amazon Linux AMI 64 bit, but can easily be adopted for Windows, Mac OS X or another Linux flavour.
* [Examples](docs/examples.md) - Examples of using GeoNagios on the commandline and inside Nagios
* [API](docs/api.md) - See a list of the options you can use with GeoNagios

## Quick start

See [[Installing GeoNagios on Linux or Mac OS X]]) for list of dependencies. 

Hello world of GeoNagios:

```
curl -o check_wms.py https://raw.github.com/skipperkongen/GeoNagios/master/check_wms.py
chmod u+x check_wms.py
./check_wms.py 'http://kort.plansystem.dk/wms?servicename=wms' -n 1
```

This will check the WMS published at 'http://kort.plansystem.dk/wms?servicename=wms'. It picks a single, random layer from the layers listed in GetCapabilities, and tests it using a GetMap request.

You should see output similar to the following:

```
OK|
't_get_capabilities'=824ms,
't_max'=824ms,
't_min'=824ms,
't_theme-pdk-lavbundsareal_aflyst'=824ms,
's_theme-pdk-lavbundsareal_aflyst'=126032B
```

## Test servers (WMS)

A few public WMS services have been listed on this wiki for test purposes:

See [public WMS servers](docs/public-wms-servers.md) for a list of WMS servers to use for testing.