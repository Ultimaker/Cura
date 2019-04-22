import functools

from UM.Qt.Duration import Duration
from cura.UI import PrintInformation
from cura.Settings.MachineManager import MachineManager

from unittest.mock import MagicMock, patch
from UM.Application import Application
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType


def getPrintInformation(printer_name) -> PrintInformation:

    mock_application = MagicMock(name = "mock_application")
    mocked_preferences = MagicMock(name="mocked_preferences")
    mocked_extruder_stack = MagicMock()
    mocked_extruder_stack.getProperty = MagicMock(return_value = 3)
    mocked_material = MagicMock(name= "mocked material")
    mocked_material.getMetaDataEntry = MagicMock(return_value = "omgzomg")
    mocked_extruder_stack.material = mocked_material

    mock_application.getInstance = MagicMock(return_value = mock_application)
    mocked_preferences.getValue = MagicMock(return_value = '{"omgzomg": {"spool_weight": 10, "spool_cost": 9}}')

    global_container_stack = MagicMock()
    global_container_stack.extruders = {"0": mocked_extruder_stack}
    global_container_stack.definition.getName = MagicMock(return_value = printer_name)
    mock_application.getGlobalContainerStack = MagicMock(return_value = global_container_stack)
    mock_application.getPreferences = MagicMock(return_value = mocked_preferences)

    multi_build_plate_model = MagicMock()
    multi_build_plate_model.maxBuildPlate = 0
    mock_application.getMultiBuildPlateModel = MagicMock(return_value = multi_build_plate_model)

    # Mock-up the entire machine manager except the function that needs to be tested: getAbbreviatedMachineName
    original_get_abbreviated_name = MachineManager.getAbbreviatedMachineName
    mock_machine_manager = MagicMock()
    mock_machine_manager.getAbbreviatedMachineName = functools.partial(original_get_abbreviated_name, mock_machine_manager)
    mock_application.getMachineManager = MagicMock(return_value = mock_machine_manager)

    Application.getInstance = MagicMock(return_value = mock_application)

    with patch("json.loads", lambda x: {}):
        print_information = PrintInformation.PrintInformation(mock_application)

    return print_information


def setup_module():
     MimeTypeDatabase.addMimeType(
        MimeType(
            name = "application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
            comment = "3MF",
            suffixes = ["3mf"]
        )
     )

     MimeTypeDatabase.addMimeType(
         MimeType(
             name = "application/x-cura-gcode-file",
             comment = "Cura GCode File",
             suffixes = ["gcode"]
         )
     )


def test_duration():
    print_information = getPrintInformation("ultimaker")

    feature_print_times = print_information.getFeaturePrintTimes()
    assert int(feature_print_times["Travel"]) == int(Duration(None))

    # Ensure that all print times are zero-ed
    print_information.setToZeroPrintInformation()
    assert int(feature_print_times["Travel"]) == 0

    # Fake a print duration message
    print_information._onPrintDurationMessage(0, {"travel": 20}, [10])

    # We only set a single time, so the total time must be of the same value.
    assert int(print_information.currentPrintTime) == 20

    feature_print_times = print_information.getFeaturePrintTimes()
    assert int(feature_print_times["Travel"]) == 20

    print_information.setToZeroPrintInformation()
    assert int(feature_print_times["Travel"]) == 0


def test_setProjectName():

    print_information = getPrintInformation("ultimaker")

    # Test simple name
    project_name = ["HelloWorld", ".3mf"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert "UM_" + project_name[0] == print_information._job_name

    # Test the name with one dot
    project_name = ["Hello.World", ".3mf"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert "UM_" + project_name[0] == print_information._job_name

    # Test the name with two dot
    project_name = ["Hello.World.World", ".3mf"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert "UM_" + project_name[0] == print_information._job_name

    # Test the name with dot at the beginning
    project_name = [".Hello.World", ".3mf"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert "UM_" + project_name[0] == print_information._job_name

    # Test the name with underline
    project_name = ["Hello_World", ".3mf"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert "UM_" + project_name[0] == print_information._job_name

    # Test gcode extension
    project_name = ["Hello_World", ".gcode"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert "UM_" + project_name[0] == print_information._job_name

    # Test empty project name
    project_name = ["", ""]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert print_information.UNTITLED_JOB_NAME == print_information._job_name

    # Test wrong file extension
    project_name = ["Hello_World", ".test"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert "UM_" + project_name[0] != print_information._job_name


def test_setJobName():

    print_information = getPrintInformation("ultimaker")

    print_information._abbr_machine = "UM"
    print_information.setJobName("UM_HelloWorld", is_user_specified_job_name = False)


def test_defineAbbreviatedMachineName():
    printer_name = "Test"

    print_information = getPrintInformation(printer_name)

    # Test not ultimaker printer, name suffix should have first letter from the printer name
    project_name = ["HelloWorld", ".3mf"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert printer_name[0] + "_" + project_name[0] == print_information._job_name