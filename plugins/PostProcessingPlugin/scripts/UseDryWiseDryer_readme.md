

# Motivation

This script is a highly requested feature from our clients. Normally, the dryer requires manual loading of the
filament in the printer 40 mins after starting drying and manually starting the print 20 mins after loading.
This means that the user must be nearby the dryer for up to 1 hour after starting drying. This is inconvenient because:
1. It is distracting, especially when using multiple dryers.
2. You cannot start the print last minute before you leave work.
3. One may forget about the dryer, and as a result the model will not get printed at all.

This script attempts to resolve these issues by providing a more automated method of drying and printing, at
the cost of ~2 g of purged wet filament (depending of the printer and dryer setup)

## How the script works

1. The wet filament is passed through the dryer and is attached to the extruder. Notice that the filament is **not** loaded in the printer, but the end of the filament is gripped by the extruder gear.
2. The dryer is switched on and put in the printing mode, the print file is selected and the printer starts printing immediately.
3. The script loads the filament in the printer, meaning that the printer moves the filament until it reaches the 
nozzle. The loading is done roughly at the printing speed defined by the slicer to ensure that the filament is
dried uniformly.
4. The loaded filament is wet, because it was not processed by the dryer. This filament now needs to be purged, so
a purge cube is printed at the edge of the buildplate. The purge cube is printed until all unprocessed material is
removed.
5. The loaded filament is now dry. The printer begins printing the sliced model using the dried material. At the 
same time, the dryer is continuing drying the material.


## How to install the script

It is expected that in the future versions no installation will be necessary as cura will integrate this script 
with the `PostProcessingPlugin` and make it available for all clients. Until then, the script has to be installed
according to the following procedure:
1. Download `UseDrywiseDryer.py`. Any other files in the repository are not required for proper functioning of the
script.
2. Locate your cura installation folder. Normally, it is installed in 
`C:\Program Files\UltiMaker Cura {version_number}`. 
3. In the cura directory find the folder `~\share\cura\plugins\PostProcessingPlugin\scripts` and put the script file(s) there.
4. Restart cura (if already running). You are now ready to use the script.

## How to use the script

### Slicing
1. Launch cura.
2. Add your models and choose your printing profile
2. Go to `Extensions/Post Processing/Modify G-code`.
3. Click `Add a script` button and select `Use Drywise Dryer`. It is usually located at the bottom of all scripts.
4. Enter the required parameters. For the printer that we have tested, the "Distance from extruder to nozzle" 
parameter is already pre-defined. However, the "Distance from dryer output to extruder" depends on your set-up,
you will need to work it out yourself. See [Explanation of script parameters] section on the explanation of
individual parameters as well as how to choose them.
5. Close the script window and slice the model.
6. Unforturnately, for now the purging cube is not shown in the "Preview". This is one of the current limitations
on the script that will be addressed soon. However, you will be able to see the purging cube when viewing the gcode
directly. Save the gcode and drag and drop it in the cura application.
7. Ensure that the purge cube does not overlap with your model. If it does, then you will need to move your models
away from the location where the purging cube will be printed and reslice the file again.
8. You are now ready to print your model.

### Drying and printing
1. Start the dryer and select the material to be dried. 
2. Press "Start" to move to the filament loading screen. Sharpen the filament and pass it through the dryer, 
like during normal operation. When you have done so, press "Next" on the dryer to finish loading procedure.
2. Pull the filament out of the dryer and place it inside the extruder s.t. the extruder gear grips it firmly. 
Ensure that the extruder managed to grip the filament. You might want to test this by trying to pull 
the filament out of the extruder gear. **Note: do not load the filament all the way to the nozzle. 
If you do so, you may damage your printer. The printer will load the filament automatically during operation.**
3. Position the dryer close to the printer, like during normal operation.
4. Due to the way the script works, you will need to enter the continuous cycle immediately. At the moment, you
should be at the "Pre-Drying Cycle" screen with the following buttons available: "Start", "Abort", and "Skip".
To enter the continuous cycle immediately press the following buttons in the following sequence:
> "Skip" > "Skip Pre-Drying" > "Skip" > "Skip Loading" > "Skip" > "Skip Preparing" > "Print started".
5. You should now be at the printing screen, which you normally see when the printer is printing and the dryer
is drying the filament as it is being extruded by the printer.
5. Select your print file on your printer and start printing normally.
6. You may return to whatever you are working on.

## Explanation of script parameters
- **Extruder in Use**: Which extruder is connected to the dryer
- **Distance from extruder to nozzle**: Self-explanatory. Notice that this value is usually constant among printers
  of the same model. As a result, we provide some preset values for the printers that we have tested.
- **Distance from dryer output to extruder**: Self-explanatory. This value is highly dependent on your printer-drywise
  set up, therefore we leave it up to you to measure it.
- **Position of the purge cube**: Allows you to choose on which side of the buildplate the purge cube is printed.
- **Cube height**: By default, the cube height is 1.5 mm. Please, review the Issue #1, which describes our motivations
for why it was not made any larger.

To measure the `Distance from extruder to nozzle` parameter, load the filament into the printer, mark the location of
the extruder gear as close as you can, extract the filament and measure the distance between the filament tip
      

# Current limitations
 - The purge cube does not appear in the "Prepare" and "Preview" tabs
 - There is no check for whether the model is printed too close to the purge cube
 - Two separate gcodes need to be sliced (one with the script and one without).     
 - Wet filament has to be purged. This results in wasted material and money. However:
   1. Your time and attention may be worth more than purged material. After all, this is why you
      bought Drywise - to stop worrying about wet filament and focus on important work.
   2. The amount of purged material is constant regardless of the length of the print. Consequently,
      the larger the print, the smaller relative amount of material is wasted. As an example, for Ultimaker printers and
      Ender S1 Pro, the amount of material purged is ~2.0 g, therefore when printing a somewhat large model weighing 70 g,
      only 2.8% of the printed material is wasted.
   3. After printing the filament inside the printer and the dryer stay dry for some time. As a
      result, you may continue printing later in the day without purging any more material. However, after **X** hours
      we cannot guarantee the dryness of the material


# Troubleshooting

### Material leaking out of the nozzle during loading
It appears that you have overestimated the loading length of the filament. The solution is to reduce
the value of the **Distance from extruder to nozzle** parameter.

### First layer of the purge cube looks terrible / The purge cube got detached
This could be caused by **Distance from extruder to nozzle** being too low, so when the printer starts
purging the wet material, the filament is not fully loaded. You may try to increase the value of
this parameter. 

Note that bed adhesion is a common 3d printing problem, so the script may not be at fault. Poor bed adhesion
may also be caused by:
 - Miscalibrated bed leveling and/or z offset.
 - Absense of adhesive on the buildplate

### Filament is ground in the extruder
Although unlikely, this might be caused by the script where the **Distance from extruder to nozzle** parameter
is grossly overestimated. However, it is more likely that the problem is caused by:
 - A clog in the nozzle
 - Too low nozzle temperature during printing
 - Extruder tension too small

### Material still wet even after the purge cube
If the bottom of the model is still wet, while the top is dry, then you did not purge enough wet material.
To fix this problem, increase **Distance from dryer output to extruder** accordingly.
If the whole model is still wet, then there may be a problem with your Drywise. Please, contact our support
team at support@drywise.co

### The dryer shows the "Filament stopped moving" message during loading
The "Filament stopped moving" means that the dryer sensed that the filament moved <5cm in the last 5 mins.
A possible simple solution for this problem is to check if the extruder is actually gripping the filament.
If not, then check if the filament is ground. If yes, review the "Filament is ground in the extruder" section.

Otherwise, the cause of this problem may be complex, therefore, please, contact our support
team at support@drywise.co
