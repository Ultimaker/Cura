import argparse
import re


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Extract the changelog to be inserted to the release description')
    parser.add_argument('--changelog', type = str, help = 'Path to the changelog file', required = True)
    parser.add_argument('--version', type = str, help = 'Cura version to be extracted', required = True)
    args = parser.parse_args()

    # In the changelog we usually omit the patch number for minor release (i.e. 5.7.0 => 5.7)
    if args.version.endswith('.0'):
        args.version = args.version[:-2]

    start_token = f"[{args.version}]"
    pattern_stop_log = "\[\d+(\.\d+){1,2}\]"
    log_line = False
    first_chapter = True

    with open(args.changelog, "r") as changelog_file:
        for line in changelog_file.readlines():
            line = line.strip()

            if log_line:
                if re.match(pattern_stop_log, line):
                    log_line = False
                elif len(line) > 0:
                    if line.startswith('*'):
                        if not first_chapter:
                            print("")
                        first_chapter = False

                        line = line[1:].strip()
                        print(f"<H2>{line}</H2>\n")
                    else:
                        print(line)
            elif line == start_token:
                log_line = True
