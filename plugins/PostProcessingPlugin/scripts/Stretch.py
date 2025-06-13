# This PostProcessingPlugin script is released under the terms of the LGPLv3 or higher.
"""
Copyright (c) 2017 Christophe Baribaud 2017
Python implementation of https://github.com/electrocbd/post_stretch
Correction of hole sizes, cylinder diameters and curves
See the original description in https://github.com/electrocbd/post_stretch

WARNING This script has never been tested with several extruders
"""
from ..Script import Script
import numpy as np
from UM.Logger import Logger
import re
from cura.Settings.ExtruderManager import ExtruderManager


def _getValue(line, key, default=None):
    """
    Convenience function that finds the value in a line of g-code.
    When requesting key = x from line "G1 X100" the value 100 is returned.
    It is a copy of Stript's method, so it is no DontRepeatYourself, but
    I split the class into setup part (Stretch) and execution part (Strecher)
    and only the setup part inherits from Script
    """
    if not key in line or (";" in line and line.find(key) > line.find(";")):
        return default
    sub_part = line[line.find(key) + 1:]
    number = re.search(r"^-?[0-9]+\.?[0-9]*", sub_part)
    if number is None:
        return default
    return float(number.group(0))


class GCodeStep():
    """
    Class to store the current value of each G_Code parameter
    for any G-Code step
    """
    def __init__(self, step, in_relative_movement: bool = False) -> None:
        self.step = step
        self.step_x = 0
        self.step_y = 0
        self.step_z = 0
        self.step_e = 0
        self.step_f = 0

        self.in_relative_movement = in_relative_movement

        self.comment = ""

    def readStep(self, line):
        """
        Reads gcode from line into self
        """
        if not self.in_relative_movement:
            self.step_x = _getValue(line, "X", self.step_x)
            self.step_y = _getValue(line, "Y", self.step_y)
            self.step_z = _getValue(line, "Z", self.step_z)
            self.step_e = _getValue(line, "E", self.step_e)
            self.step_f = _getValue(line, "F", self.step_f)
        else:
            delta_step_x = _getValue(line, "X", 0)
            delta_step_y = _getValue(line, "Y", 0)
            delta_step_z = _getValue(line, "Z", 0)
            delta_step_e = _getValue(line, "E", 0)

            self.step_x += delta_step_x
            self.step_y += delta_step_y
            self.step_z += delta_step_z
            self.step_e += delta_step_e
            self.step_f = _getValue(line, "F", self.step_f)  # the feedrate is not relative

    def copyPosFrom(self, step):
        """
        Copies positions of step into self
        """
        self.step_x = step.step_x
        self.step_y = step.step_y
        self.step_z = step.step_z
        self.step_e = step.step_e
        self.step_f = step.step_f
        self.comment = step.comment

    def setInRelativeMovement(self, value: bool) -> None:
        self.in_relative_movement = value


# Execution part of the stretch plugin
class Stretcher:
    """
    Execution part of the stretch algorithm
    """
    def __init__(self, line_width, wc_stretch, pw_stretch):
        self.line_width = line_width
        self.wc_stretch = wc_stretch
        self.pw_stretch = pw_stretch
        if self.pw_stretch > line_width / 4:
            self.pw_stretch = line_width / 4 # Limit value of pushwall stretch distance
        self.outpos = GCodeStep(0)
        self.vd1 = np.empty((0, 2)) # Start points of segments
                                    # of already deposited material for current layer
        self.vd2 = np.empty((0, 2)) # End points of segments
                                    # of already deposited material for current layer
        self.layer_z = 0            # Z position of the extrusion moves of the current layer
        self.layergcode = ""
        self._in_relative_movement = False

    def execute(self, data):
        """
        Computes the new X and Y coordinates of all g-code steps
        """
        Logger.log("d", "Post stretch with line width " + str(self.line_width)
                   + "mm wide circle stretch " + str(self.wc_stretch)+ "mm"
                   + " and push wall stretch " + str(self.pw_stretch) + "mm")
        retdata = []
        layer_steps = []
        in_relative_movement = False
        current = GCodeStep(0, in_relative_movement)
        self.layer_z = 0.
        current_e = 0.
        for layer in data:
            lines = layer.rstrip("\n").split("\n")
            for line in lines:
                current.comment = ""
                if line.find(";") >= 0:
                    current.comment = line[line.find(";"):]
                if _getValue(line, "G") == 0:
                    current.readStep(line)
                    onestep = GCodeStep(0, in_relative_movement)
                    onestep.copyPosFrom(current)
                elif _getValue(line, "G") == 1:
                    last_x = current.step_x
                    last_y = current.step_y
                    last_z = current.step_z
                    last_e = current.step_e
                    current.readStep(line)
                    if (current.step_x == last_x and current.step_y == last_y and
                        current.step_z == last_z and current.step_e != last_e
                    ):
                        # It's an extruder only move. Preserve it rather than process it as an
                        # extruded move. Otherwise, the stretched output might contain slight
                        # motion in X and Y in addition to E. This can cause problems with
                        # firmwares that implement pressure advance.
                        onestep = GCodeStep(-1, in_relative_movement)
                        onestep.copyPosFrom(current)
                        # Rather than copy the original line, write a new one with consistent
                        # extruder coordinates
                        onestep.comment = "G1 F{} E{}".format(onestep.step_f, onestep.step_e)
                    else:
                        onestep = GCodeStep(1, in_relative_movement)
                        onestep.copyPosFrom(current)

                # end of relative movement
                elif _getValue(line, "G") == 90:
                    in_relative_movement = False
                    current.setInRelativeMovement(in_relative_movement)
                # start of relative movement
                elif _getValue(line, "G") == 91:
                    in_relative_movement = True
                    current.setInRelativeMovement(in_relative_movement)

                elif _getValue(line, "G") == 92:
                    current.readStep(line)
                    onestep = GCodeStep(-1, in_relative_movement)
                    onestep.copyPosFrom(current)
                    onestep.comment = line
                else:
                    onestep = GCodeStep(-1, in_relative_movement)
                    onestep.copyPosFrom(current)
                    onestep.comment = line

                if line.find(";LAYER:") >= 0 and len(layer_steps):
                    # Previous plugin "forgot" to separate two layers...
                    Logger.log("d", "Layer Z " + "{:.3f}".format(self.layer_z)
                               + " " + str(len(layer_steps)) + " steps")
                    retdata.append(self.processLayer(layer_steps))
                    layer_steps = []
                layer_steps.append(onestep)
                # self.layer_z is the z position of the last extrusion move (not travel move)
                if current.step_z != self.layer_z and current.step_e != current_e:
                    self.layer_z = current.step_z
                current_e = current.step_e
            if len(layer_steps): # Force a new item in the array
                Logger.log("d", "Layer Z " + "{:.3f}".format(self.layer_z)
                           + " " + str(len(layer_steps)) + " steps")
                retdata.append(self.processLayer(layer_steps))
                layer_steps = []
        retdata.append(";Wide circle stretch distance " + str(self.wc_stretch) + "\n")
        retdata.append(";Push wall stretch distance " + str(self.pw_stretch) + "\n")
        return retdata

    def extrusionBreak(self, layer_steps, i_pos):
        """
        Returns true if the command layer_steps[i_pos] breaks the extruded filament
        i.e. it is a travel move
        """
        if i_pos == 0:
            return True # Beginning a layer always breaks filament (for simplicity)
        step = layer_steps[i_pos]
        prev_step = layer_steps[i_pos - 1]
        if step.step_e != prev_step.step_e:
            return False
        delta_x = step.step_x - prev_step.step_x
        delta_y = step.step_y - prev_step.step_y
        if delta_x * delta_x + delta_y * delta_y < self.line_width * self.line_width / 4:
            # This is a very short movement, less than 0.5 * line_width
            # It does not break filament, we should stay in the same extrusion sequence
            return False
        return True # New sequence

    def processLayer(self, layer_steps):
        """
        Computes the new coordinates of g-code steps
        for one layer (all the steps at the same Z coordinate)
        """
        self.outpos.step_x = -1000 # Force output of X and Y coordinates
        self.outpos.step_y = -1000 # at each start of layer
        self.layergcode = ""
        self.vd1 = np.empty((0, 2))
        self.vd2 = np.empty((0, 2))
        orig_seq = np.empty((0, 2))
        modif_seq = np.empty((0, 2))
        iflush = 0
        for i, step in enumerate(layer_steps):
            if step.step == 0 or step.step == 1:
                if self.extrusionBreak(layer_steps, i):
                    # No extrusion since the previous step, so it is a travel move
                    # Let process steps accumulated into orig_seq,
                    # which are a sequence of continuous extrusion
                    modif_seq = np.copy(orig_seq)
                    if len(orig_seq) >= 2:
                        self.workOnSequence(orig_seq, modif_seq)
                    self.generate(layer_steps, iflush, i, modif_seq)
                    iflush = i
                    orig_seq = np.empty((0, 2))
                orig_seq = np.concatenate([orig_seq, np.array([[step.step_x, step.step_y]])])
        if len(orig_seq):
            modif_seq = np.copy(orig_seq)
        if len(orig_seq) >= 2:
            self.workOnSequence(orig_seq, modif_seq)
        self.generate(layer_steps, iflush, len(layer_steps), modif_seq)
        return self.layergcode

    def stepToGcode(self, onestep):
        """
        Converts a step into G-Code
        For each of the X, Y, Z, E and F parameter,
        the parameter is written only if its value changed since the
        previous g-code step.
        """
        sout = ""
        if onestep.step_f != self.outpos.step_f:
            self.outpos.step_f = onestep.step_f
            sout += " F{:.0f}".format(self.outpos.step_f).rstrip(".")
        if onestep.step_x != self.outpos.step_x or onestep.step_y != self.outpos.step_y:
            assert onestep.step_x >= -1000 and onestep.step_x < 1000 # If this assertion fails,
                                                           # something went really wrong !
            self.outpos.step_x = onestep.step_x
            sout += " X{:.3f}".format(self.outpos.step_x).rstrip("0").rstrip(".")
            assert onestep.step_y >= -1000 and onestep.step_y < 1000 # If this assertion fails,
                                                           # something went really wrong !
            self.outpos.step_y = onestep.step_y
            sout += " Y{:.3f}".format(self.outpos.step_y).rstrip("0").rstrip(".")
        if onestep.step_z != self.outpos.step_z or onestep.step_z != self.layer_z:
            self.outpos.step_z = onestep.step_z
            sout += " Z{:.3f}".format(self.outpos.step_z).rstrip("0").rstrip(".")
        if onestep.step_e != self.outpos.step_e:
            self.outpos.step_e = onestep.step_e
            sout += " E{:.5f}".format(self.outpos.step_e).rstrip("0").rstrip(".")
        return sout

    def generate(self, layer_steps, ibeg, iend, orig_seq):
        """
        Appends g-code lines to the plugin's returned string
        starting from step ibeg included and until step iend excluded
        """
        ipos = 0
        for i in range(ibeg, iend):
            if layer_steps[i].step == 0:
                layer_steps[i].step_x = orig_seq[ipos][0]
                layer_steps[i].step_y = orig_seq[ipos][1]
                sout = "G0" + self.stepToGcode(layer_steps[i])
                self.layergcode = self.layergcode + sout + "\n"
                ipos = ipos + 1
            elif layer_steps[i].step == 1:
                layer_steps[i].step_x = orig_seq[ipos][0]
                layer_steps[i].step_y = orig_seq[ipos][1]
                sout = "G1" + self.stepToGcode(layer_steps[i])
                self.layergcode = self.layergcode + sout + "\n"
                ipos = ipos + 1
            else:
                # The command is intended to be passed through unmodified via
                # the comment field. In the case of an extruder only move, though,
                # the extruder and potentially the feed rate are modified.
                # We need to update self.outpos accordingly so that subsequent calls
                # to stepToGcode() knows about the extruder and feed rate change.
                self.outpos.step_e = layer_steps[i].step_e
                self.outpos.step_f = layer_steps[i].step_f
                self.layergcode = self.layergcode + layer_steps[i].comment + "\n"

    def workOnSequence(self, orig_seq, modif_seq):
        """
        Computes new coordinates for a sequence
        A sequence is a list of consecutive g-code steps
        of continuous material extrusion
        """
        d_contact = self.line_width / 2.0
        if (len(orig_seq) > 2 and
                ((orig_seq[len(orig_seq) - 1] - orig_seq[0]) ** 2).sum(0) < d_contact * d_contact):
            # Starting and ending point of the sequence are nearby
            # It is a closed loop
            #self.layergcode = self.layergcode + ";wideCircle\n"
            self.wideCircle(orig_seq, modif_seq)
        else:
            #self.layergcode = self.layergcode + ";wideTurn\n"
            self.wideTurn(orig_seq, modif_seq) # It is an open curve
        if len(orig_seq) > 6: # Don't try push wall on a short sequence
            self.pushWall(orig_seq, modif_seq)
        if len(orig_seq):
            self.vd1 = np.concatenate([self.vd1, np.array(orig_seq[:-1])])
            self.vd2 = np.concatenate([self.vd2, np.array(orig_seq[1:])])

    def wideCircle(self, orig_seq, modif_seq):
        """
        Similar to wideTurn
        The first and last point of the sequence are the same,
        so it is possible to extend the end of the sequence
        with its beginning when seeking for triangles

        It is necessary to find the direction of the curve, knowing three points (a triangle)
        If the triangle is not wide enough, there is a huge risk of finding
        an incorrect orientation, due to insufficient accuracy.
        So, when the consecutive points are too close, the method
        use following and preceding points to form a wider triangle around
        the current point
        dmin_tri is the minimum distance between two consecutive points
        of an acceptable triangle
        """
        dmin_tri = 0.5
        iextra_base = np.floor_divide(len(orig_seq), 3) # Nb of extra points
        ibeg = 0 # Index of first point of the triangle
        iend = 0 # Index of the third point of the triangle
        for i, step in enumerate(orig_seq):
            if i == 0 or i == len(orig_seq) - 1:
                # First and last point of the sequence are the same,
                # so it is necessary to skip one of these two points
                # when creating a triangle containing the first or the last point
                iextra = iextra_base + 1
            else:
                iextra = iextra_base
            # i is the index of the second point of the triangle
            # pos_after is the array of positions of the original sequence
            # after the current point
            pos_after = np.resize(np.roll(orig_seq, -i-1, 0), (iextra, 2))
            # Vector of distances between the current point and each following point
            dist_from_point = ((step - pos_after) ** 2).sum(1)
            if np.amax(dist_from_point) < dmin_tri * dmin_tri:
                continue
            iend = np.argmax(dist_from_point >= dmin_tri * dmin_tri)
            # pos_before is the array of positions of the original sequence
            # before the current point
            pos_before = np.resize(np.roll(orig_seq, -i, 0)[::-1], (iextra, 2))
            # This time, vector of distances between the current point and each preceding point
            dist_from_point = ((step - pos_before) ** 2).sum(1)
            if np.amax(dist_from_point) < dmin_tri * dmin_tri:
                continue
            ibeg = np.argmax(dist_from_point >= dmin_tri * dmin_tri)
            # See https://github.com/electrocbd/post_stretch for explanations
            # relpos is the relative position of the projection of the second point
            # of the triangle on the segment from the first to the third point
            # 0 means the position of the first point, 1 means the position of the third,
            # intermediate values are positions between
            length_base = ((pos_after[iend] - pos_before[ibeg]) ** 2).sum(0)
            relpos = ((step - pos_before[ibeg])
                      * (pos_after[iend] - pos_before[ibeg])).sum(0)
            if np.fabs(relpos) < 1000.0 * np.fabs(length_base):
                relpos /= length_base
            else:
                relpos = 0.5 # To avoid division by zero or precision loss
            projection = (pos_before[ibeg] + relpos * (pos_after[iend] - pos_before[ibeg]))
            dist_from_proj = np.sqrt(((projection - step) ** 2).sum(0))
            if dist_from_proj > 0.0003: # Move central point only if points are not aligned
                modif_seq[i] = (step - (self.wc_stretch / dist_from_proj)
                                * (projection - step))

        return

    def wideTurn(self, orig_seq, modif_seq):
        '''
        We have to select three points in order to form a triangle
        These three points should be far enough from each other to have
        a reliable estimation of the orientation of the current turn
        '''
        dmin_tri = self.line_width / 2.0
        ibeg = 0
        iend = 2
        for i in range(1, len(orig_seq) - 1):
            dist_from_point = ((orig_seq[i] - orig_seq[i+1:]) ** 2).sum(1)
            if np.amax(dist_from_point) < dmin_tri * dmin_tri:
                continue
            iend = i + 1 + np.argmax(dist_from_point >= dmin_tri * dmin_tri)
            dist_from_point = ((orig_seq[i] - orig_seq[i-1::-1]) ** 2).sum(1)
            if np.amax(dist_from_point) < dmin_tri * dmin_tri:
                continue
            ibeg = i - 1 - np.argmax(dist_from_point >= dmin_tri * dmin_tri)
            length_base = ((orig_seq[iend] - orig_seq[ibeg]) ** 2).sum(0)
            relpos = ((orig_seq[i] - orig_seq[ibeg]) * (orig_seq[iend] - orig_seq[ibeg])).sum(0)
            if np.fabs(relpos) < 1000.0 * np.fabs(length_base):
                relpos /= length_base
            else:
                relpos = 0.5
            projection = orig_seq[ibeg] + relpos * (orig_seq[iend] - orig_seq[ibeg])
            dist_from_proj = np.sqrt(((projection - orig_seq[i]) ** 2).sum(0))
            if dist_from_proj > 0.001:
                modif_seq[i] = (orig_seq[i] - (self.wc_stretch / dist_from_proj)
                                * (projection - orig_seq[i]))
        return

    def pushWall(self, orig_seq, modif_seq):
        """
        The algorithm tests for each segment if material was
        already deposited at one or the other side of this segment.
        If material was deposited at one side but not both,
        the segment is moved into the direction of the deposited material,
        to "push the wall"

        Already deposited material is stored as segments.
        vd1 is the array of the starting points of the segments
        vd2 is the array of the ending points of the segments
        For example, segment nr 8 starts at position self.vd1[8]
        and ends at position self.vd2[8]
        """
        dist_palp = self.line_width # Palpation distance to seek for a wall
        mrot = np.array([[0, -1], [1, 0]]) # Rotation matrix for a quarter turn
        for i, _ in enumerate(orig_seq):
            ibeg = i # Index of the first point of the segment
            iend = i + 1 # Index of the last point of the segment
            if iend == len(orig_seq):
                iend = i - 1
            xperp = np.dot(mrot, orig_seq[iend] - orig_seq[ibeg])
            xperp = xperp / np.sqrt((xperp ** 2).sum(-1))
            testleft = orig_seq[ibeg] + xperp * dist_palp
            materialleft = False # Is there already extruded material at the left of the segment
            testright = orig_seq[ibeg] - xperp * dist_palp
            materialright = False # Is there already extruded material at the right of the segment
            if self.vd1.shape[0]:
                relpos = np.clip(((testleft - self.vd1) * (self.vd2 - self.vd1)).sum(1)
                                 / ((self.vd2 - self.vd1) * (self.vd2 - self.vd1)).sum(1), 0., 1.)
                nearpoints = self.vd1 + relpos[:, np.newaxis] * (self.vd2 - self.vd1)
                # nearpoints is the array of the nearest points of each segment
                # from the point testleft
                dist = ((testleft - nearpoints) * (testleft - nearpoints)).sum(1)
                # dist is the array of the squares of the distances between testleft
                # and each segment
                if np.amin(dist) <= dist_palp * dist_palp:
                    materialleft = True
                # Now the same computation with the point testright at the other side of the
                # current segment
                relpos = np.clip(((testright - self.vd1) * (self.vd2 - self.vd1)).sum(1)
                                 / ((self.vd2 - self.vd1) * (self.vd2 - self.vd1)).sum(1), 0., 1.)
                nearpoints = self.vd1 + relpos[:, np.newaxis] * (self.vd2 - self.vd1)
                dist = ((testright - nearpoints) * (testright - nearpoints)).sum(1)
                if np.amin(dist) <= dist_palp * dist_palp:
                    materialright = True
            if materialleft and not materialright:
                modif_seq[ibeg] = modif_seq[ibeg] + xperp * self.pw_stretch
            elif not materialleft and materialright:
                modif_seq[ibeg] = modif_seq[ibeg] - xperp * self.pw_stretch

# Setup part of the stretch plugin
class Stretch(Script):
    """
    Setup part of the stretch algorithm
    The only parameter is the stretch distance
    """
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"Post stretch script",
            "key": "Stretch",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "wc_stretch":
                {
                    "label": "Wide circle stretch distance",
                    "description": "Distance by which the points are moved by the correction effect in corners. The higher this value, the higher the effect",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.1,
                    "minimum_value": 0,
                    "minimum_value_warning": 0,
                    "maximum_value_warning": 0.2
                },
                "pw_stretch":
                {
                    "label": "Push Wall stretch distance",
                    "description": "Distance by which the points are moved by the correction effect when two lines are nearby. The higher this value, the higher the effect",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.1,
                    "minimum_value": 0,
                    "minimum_value_warning": 0,
                    "maximum_value_warning": 0.2
                }
            }
        }"""

    def execute(self, data):
        """
        Entry point of the plugin.
        data is the list of original g-code instructions,
        the returned string is the list of modified g-code instructions
        """
        stretcher = Stretcher(
            ExtruderManager.getInstance().getActiveExtruderStack().getProperty("machine_nozzle_size", "value")
            , self.getSettingValueByKey("wc_stretch"), self.getSettingValueByKey("pw_stretch"))
        return stretcher.execute(data)

