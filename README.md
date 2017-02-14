# OctoPrintPlugin
Cura plugin which enables printing directly to OctoPrint and monitoring the progress

This plugin started out as a fork of the UM3NetworkPrinting plugin:
https://github.com/Ultimaker/UM3NetworkPrintingPlugin

Installation
----
* Manually:
  - Make sure your Cura version is 2.2 or newer
  - Download or clone the repository into [Cura installation folder]/plugins/OctoPrintPlugin 
    or in the plugins folder inside the configuration folder. The configuration folder can be
    found via Help -> Show Configuration Folder inside Cura.
    NB: The folder of the plugin itself *must* be ```OctoPrintPlugin```
    NB: Make sure you download the branch that matches the Cura branch (ie: 2.4 for Cura 2.4 etc)
  - If you are running Cura from source, make sure you install python-zeroconf using pip: 
    ```pip3 install python3-zeroconf```.
    Released versions of Cura already meet this requirement.
* Cura PPA (*Ubuntu):
  - Add the cura PPA via (if not already done): `sudo add-apt-repository ppa:thopiekar/cura`
  - Update APT via: `sudo apt update`
  - Install the plugin via: `sudo apt install cura-extra-plugin-octoprint`
  

How to use
----
- Make sure OctoPrint is up and running, and the discovery plugin is not disabled
- In Cura, add a Printer matching the 3d printer you have connected to OctoPrint
- Select "Connect to OctoPrint" on the Manage Printers page.
- Select your OctoPrint instance from the list and enter the API key which is
  available in the OctoPrint settings.
- From this point on, the print monitor should be functional and you should be
  able to switch to "Print to Octoprint" on the bottom of the sidebar.

Notes on UltiGCode (Ultimaker 2/Ultimaker 2+)
----
The Ultimaker 2(+) family uses a flavor of GCode named UltiGCode. Unfortunately printing
using UltiGCode flavor does not work when printing over the USB connection. That is why
using OctoPrint does not work with UltiGCode flavor.

For the Ultimaker 2/Ultimaker 2 Extended, you can use "Machine Settings" on the
"Printers" pane of the preferences to change your GCode flavor to "RepRap 
(Marlin/Sprinter)".

The Ultimaker 2+/Ultimaker 2 Extended+ currently don't support "Machine Settings". You
can use one of these alternative printer definitions instead:
<dl>
<dt>Ultimaker2+</dt>
<dd>https://gist.github.com/fieldOfView/bf536254add126fd4c7b36bc347fce73</dd>
<dt>Ultimaker2 Extended+</dt>
<dd>https://gist.github.com/fieldOfView/a52caf946d0a0df522c22298a6c94209</dd>
</dl>
Copy these files into the resources/definitions folder of your Cura application.
Restart Cura and add a new printer. You should see the option to add a Ultimaker
2+ (RepRap) and/or Ultimaker 2 Extended+ (RepRap) (depending on which file(s)
you installed.
