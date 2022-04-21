
How to Profile Cura and See What It is Doing
============================================
Cura has a simple flame graph profiler available as a plugin which can be used to see what Cura is doing as it runs and how much time it takes. A flame graph profile shows its output as a timeline and stacks of "blocks" which represent parts of the code and are stacked up to show call depth. These often form little peaks which look like flames. It is a simple yet powerful way to visualise the activity of a program.


Setting up and installing the profiler
--------------------------------------

The profiler plugin is kept outside of the Cura source code here: https://github.com/sedwards2009/cura-big-flame-graph

To install it do:

* Use `git clone https://github.com/sedwards2009/cura-big-flame-graph.git` to grab a copy of the code.
* Copy the `BigFlameGraph` directory into the `plugins` directory in your local Cura.
* Set the `URANIUM_FLAME_PROFILER` environment variable to something before starting Cura. This flags to the profiler code in Cura to activate and insert the needed hooks into the code.


Using the profiler
------------------
To open the profiler go to the Extensions menu and select "Start BFG" from the "Big Flame Graph" menu. A page will open up in your default browser. This is the profiler UI. Click on "Record" to start recording, go to Cura and perform an action and then back in the profiler click on "Stop". The results should now load in.

The time scale is at the top of the window. The blocks should be read as meaning the blocks at the bottom call the blocks which are stacked on top of them. Hover the mouse to get more detailed information about a block such as the name of the code involved and its duration. Use the zoom buttons or mouse wheel to zoom in. The display can be panned by dragging with the left mouse button.

Note: The profiler front-end itself is quite "heavy" (ok, not optimised). It runs much better in Google Chrome or Chromium than Firefox. It is also a good idea to keep recording sessions short for the same reason.


What the Profiler Sees
----------------------
The profiler doesn't capture every function call in Cura. It hooks into a number of important systems which give a good picture of activity without too much run time overhead. The most important system is Uranium's signal mechanism and PyQt5 slots. Functions which are called via the signal mechanism are recorded and their names appear in the results. PyQt5 slots appear in the results with the prefix `[SLOT]`.

Note that not all slots are captured. Only those slots which belong to classes which use the `pyqtSlot` decorator from the `UM.FlameProfiler` module.


Manually adding profiling code to more detail
---------------------------------------------
It is also possible to manually add decorators to methods to make them appear in the profiler results. The `UM.FlameProfiler` module contains the `profile` decorator which can be applied to methods. There is also a `profileCall` context manager which can be used with Python's `with` statement to measure a block of code. `profileCall` takes one argument, a label to use in the results.
