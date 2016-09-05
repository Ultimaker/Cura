# OctoPrintPlugin
Cura plugin which enables printing directly to OctoPrint and monitoring the process

Installation
----
- Make sure your Cura version is 2.2 or newer
- Download or clone the repository into [Cura installation folder]/plugins/OctoPrintPlugin
- If you are running Cura from source, make sure you install python-zeroconf using pip: 
  ```pip3 install python3-zeroconf```.
  Released versions of Cura already meet this requirement.

How to use
----
- Make sure OctoPrint is up and running, and the discovery plugin is not disabled
- In Cura, add a Printer matching the 3d printer you have connected to OctoPrint
- Select "Connect to OctoPrint" on the Manage Printers page.
- Select your OctoPrint instance from the list and enter the API key which is
  available in the OctoPrint settings.
- From this point on, the print monitor should be functional and you should be
  able to switch to "Print to Octoprint" on the bottom of the sidebar.
