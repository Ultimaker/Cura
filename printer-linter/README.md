# Printer Linter
Printer linter is a python package that does linting on Cura definitions files.
Running this on your definition files will get them ready for a pull request.

## Running Locally
From the Cura root folder and pointing to the relative paths of the wanted definition files:

```python3 printer-linter/src/terminal.py "resources/definitions/flashforge_dreamer_nx.def.json" "resources/definitions/flashforge_base.def.json" --fix --format```

## Developing
### Printer Linter Rules
Inside ```.printer-linter``` you can find a list of rules. These are seperated into roughly three categories. 

1. Checks
   1. These rules are about checking if a file meets some requirements that can't be fixed by replacing its content. 
   2. An example of a check is ```diagnostic-mesh-file-extension``` this checks if a mesh file extension is acceptable.
2. Format
   1. These rules are purely about how a file is structured, not content.
   2. An example of a format rule is ```format-definition-bracket-newline``` This rule says that when assigning a dict value the bracket should go on a new line.
3. Fixes
   1. These are about the content of the file.
   2. An example of a fix is ```diagnostic-definition-redundant-override``` This removes settings that have already been defined by a parent definition

### Linters
Linters find issues within a file. There are separate linters for each type of file. The linter that is used is decided by the create function in factory.py. All linters implement the abstract class Linter.

A Linter class returns an iterator of Diagnostics, each diagnostic is an issue with the file. The diagnostics can also contain suggested fixes.

### Formatters
Formatters load a file reformat it and write it to disk. There are separate formatters for each file type. All formatters implement the abstract class Formatter.

Formatters should format based on the Format rules in .printer-linter

