#Name: Pronterface UI
#Info: Pronterface like UI for Cura
#Depend: printwindow
#Type: printwindow

# Printer UI based on the Printrun interface by Kliment.
# Printrun is GPLv3, so this file, and the used images are GPLv3

setImage('image.png', 'map.png')

# Move X
addColorCommand(0, 0, 255, sendMovementGCode, "G91; G1 X100 F2000; G90")
addColorCommand(0, 0, 240, sendMovementGCode, "G91; G1 X10 F2000; G90")
addColorCommand(0, 0, 220, sendMovementGCode, "G91; G1 X1 F2000; G90")
addColorCommand(0, 0, 200, sendMovementGCode, "G91; G1 X0.1 F2000; G90")
addColorCommand(0, 0, 180, sendMovementGCode, "G91; G1 X-0.1 F2000; G90")
addColorCommand(0, 0, 160, sendMovementGCode, "G91; G1 X-1 F2000; G90")
addColorCommand(0, 0, 140, sendMovementGCode, "G91; G1 X-10 F2000; G90")
addColorCommand(0, 0, 120, sendMovementGCode, "G91; G1 X-100 F2000; G90")

# Move Y
addColorCommand(0, 255, 0, sendMovementGCode, "G91; G1 Y-100 F2000; G90")
addColorCommand(0, 240, 0, sendMovementGCode, "G91; G1 Y-10 F2000; G90")
addColorCommand(0, 220, 0, sendMovementGCode, "G91; G1 Y-1 F2000; G90")
addColorCommand(0, 200, 0, sendMovementGCode, "G91; G1 Y-0.1 F2000; G90")
addColorCommand(0, 180, 0, sendMovementGCode, "G91; G1 Y0.1 F2000; G90")
addColorCommand(0, 160, 0, sendMovementGCode, "G91; G1 Y1 F2000; G90")
addColorCommand(0, 140, 0, sendMovementGCode, "G91; G1 Y10 F2000; G90")
addColorCommand(0, 120, 0, sendMovementGCode, "G91; G1 Y100 F2000; G90")

# Move Z
addColorCommand(255, 0, 0, sendMovementGCode, "G91; G1 Z10 F200; G90")
addColorCommand(220, 0, 0, sendMovementGCode, "G91; G1 Z1 F200; G90")
addColorCommand(200, 0, 0, sendMovementGCode, "G91; G1 Z0.1 F200; G90")
addColorCommand(180, 0, 0, sendMovementGCode, "G91; G1 Z-0.1 F200; G90")
addColorCommand(160, 0, 0, sendMovementGCode, "G91; G1 Z-1 F200; G90")
addColorCommand(140, 0, 0, sendMovementGCode, "G91; G1 Z-10 F200; G90")

# Extrude/Retract
addColorCommand(255, 80, 0, sendGCode, "G91; G1 E10 F120; G90")
addColorCommand(255, 180, 0, sendGCode, "G91; G1 E-10 F120; G90")

# Home
addColorCommand(255, 255, 0, sendMovementGCode, "G28")
addColorCommand(240, 255, 0, sendMovementGCode, "G28 X0")
addColorCommand(220, 255, 0, sendMovementGCode, "G28 Y0")
addColorCommand(200, 255, 0, sendMovementGCode, "G28 Z0")

# Set temperatures
addTextButton(180, 0, 160, 180, 0, 140, 'set', sendGCode, "M104 S%d")
addTextButton(180, 0, 180, 180, 0, 150, 'set', sendGCode, "M140 S%d")

addTerminal(255, 0, 255)
addTemperatureGraph(180, 0, 255)
addProgressbar(255, 200, 200)

addButton(0, 255, 255, 'Connect', connect)
addButton(0, 240, 255, 'Print', startPrint)
#addButton(0, 220, 255, 'Pause', pausePrint)
addButton(0, 200, 255, 'Cancel', cancelPrint)
addButton(0, 180, 255, 'Error log', showErrorLog)
addButton(0, 160, 255, "Motors Off", sendGCode, "M18;")
