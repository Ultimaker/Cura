# Copyright (c) 2017 Thomas Karl Pietrowski


class SolidWorksEnums:
    class swUserPreferenceToggle_e:
        swSTLBinaryFormat = 69

    class swDocumentTypes_e:
        swDocNONE = 0
        swDocPART = 1
        swDocASSEMBLY = 2
        swDocDRAWING = 3

    class FileTypes:
        # Enums to open files
        SWpart = 1
        SWassembly = 2
        SWdrawing = 3

    swSTLQuality = 78

    class swLengthUnit_e:
        swMM = 0
        swCM = 1
        swMETER = 2
        swINCHES = 3
        swFEET = 4
        swFEETINCHES = 5
        swANGSTROM = 6
        swNANOMETER = 7
        swMICRON = 8
        swMIL = 9
        swUIN = 10

    class swUserPreferenceIntegerValue_e:
        swExportSTLQuality = 78
        swExportStlUnits = 211

    class swSTLQuality_e:
        swSTLQuality_Coarse = 1
        swSTLQuality_Fine = 2
        swSTLQuality_Custom = 3

    class UserPreferences:
        swSTLComponentsIntoOneFile = 72
