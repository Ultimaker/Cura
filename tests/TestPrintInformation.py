
from cura import PrintInformation

from unittest.mock import MagicMock, patch
from UM.Application import Application
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType


def getPrintInformation(printer_name) -> PrintInformation:

    mock_application = MagicMock()

    global_container_stack = MagicMock()
    global_container_stack.definition.getName = MagicMock(return_value=printer_name)
    mock_application.getGlobalContainerStack = MagicMock(return_value=global_container_stack)

    multiBuildPlateModel = MagicMock()
    multiBuildPlateModel.maxBuildPlate = 0
    mock_application.getMultiBuildPlateModel = MagicMock(return_value=multiBuildPlateModel)

    Application.getInstance = MagicMock(return_type=mock_application)

    with patch("json.loads", lambda x: {}):
        print_information = PrintInformation.PrintInformation(mock_application)

    return print_information

def setup_module():
     MimeTypeDatabase.addMimeType(
        MimeType(
            name="application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
            comment="3MF",
            suffixes=["3mf"]
        )
     )

     MimeTypeDatabase.addMimeType(
         MimeType(
             name="application/x-cura-gcode-file",
             comment="Cura GCode File",
             suffixes=["gcode"]
         )
     )



def test_setProjectName():

    print_information = getPrintInformation("ultimaker")

    # Test simple name
    project_name = ["HelloWorld",".3mf"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert "UM_" + project_name[0] == print_information._job_name

    # Test the name with one dot
    project_name = ["Hello.World",".3mf"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert "UM_" + project_name[0] == print_information._job_name

    # Test the name with two dot
    project_name = ["Hello.World.World",".3mf"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert "UM_" + project_name[0] == print_information._job_name

    # Test the name with dot at the beginning
    project_name = [".Hello.World",".3mf"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert "UM_" + project_name[0] == print_information._job_name

    # Test the name with underline
    project_name = ["Hello_World",".3mf"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert "UM_" + project_name[0] == print_information._job_name

    # Test gcode extension
    project_name = ["Hello_World",".gcode"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert "UM_" + project_name[0] == print_information._job_name

    # Test empty project name
    project_name = ["",""]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert print_information.UNTITLED_JOB_NAME == print_information._job_name

    # Test wrong file extension
    project_name = ["Hello_World",".test"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert "UM_" + project_name[0] != print_information._job_name

def test_setJobName():

    print_information = getPrintInformation("ultimaker")

    print_information._abbr_machine = "UM"
    print_information.setJobName("UM_HelloWorld", is_user_specified_job_name=False)


def test_defineAbbreviatedMachineName():
    printer_name = "Test"

    print_information = getPrintInformation(printer_name)

    # Test not ultimaker printer, name suffix should have first letter from the printer name
    project_name = ["HelloWorld",".3mf"]
    print_information.setProjectName(project_name[0] + project_name[1])
    assert printer_name[0] + "_" + project_name[0] == print_information._job_name