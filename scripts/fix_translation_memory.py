##% Script to fix a corrupted Translation memory from existing po files

import os
import re
import argparse
from pathlib import Path
from fuzzywuzzy import fuzz
import xml.etree.ElementTree as ET
from xml.sax.saxutils import unescape


def load_existing_xmtm(path: Path) -> ET.Element:
    """Load existing xmtm file and return the root element"""
    tree = ET.parse(path)
    return tree.getroot()

def load_existing_po(path: Path) -> dict:
    """Load existing po file and return a dictionary of msgid and msgstr"""
    content = path.read_text(encoding="utf-8")
    content = "".join(content.splitlines()[16:])
    # TODO: check languages with plural forms
    return dict(re.findall(r'[^#]msgid.?\"+\s?([\s|\S]+?)\"*?msgstr.?\"([\s|\S]+?)\"?#', content))

def sanitize(text: str) -> str:
    """Sanitize the text"""
    # TODO: check if Digitial Factory Ultimaker etc handled correctly
    text = text.replace("\"\"", "").replace("\"#~", "")
    text = text.replace("Ultimaker", "UltiMaker")
    text = text.replace("UltiMaker Digital Library", "Ultimaker Digital Library")
    text = text.replace("UltiMaker Digital Factory", "Ultimaker Digital Factory")
    text = text.replace("UltiMaker Marketplace", "Ultimaker Marketplace")
    return unescape(text)

def main(tmx_source_path: Path, tmx_target_path: Path, i18n_path: Path):

    po_content = {}
    for file in i18n_path.rglob("*.po"):
        print(os.path.join(i18n_path, file))
        po_content[file.relative_to(i18n_path).parts[0].replace("_", "-")] = load_existing_po(Path(os.path.join(i18n_path, file)))

    root = load_existing_xmtm(tmx_source_path)
    root_old = ET.ElementTree(root)
    # ET.indent(root_old, '  ')
    root_old.write("old.tmx", encoding="utf-8", xml_declaration=True)
    to_be_removed = []
    for tu in root.iter("tu"):
        # TODO: also add logic for other pot files
        if [t.text for t in tu.findall("prop") if t.attrib["type"] == "x-smartling-file"][0] not in ("cura.pot", "fdmprinter.def.json.pot", "fdmextruder.def.json.pot", "uranium.pot"):
            continue
        tuvs = tu.findall("tuv")
        key_source = tuvs[0].find("seg").text
        key_lang = tuvs[1].attrib["{http://www.w3.org/XML/1998/namespace}lang"]
        if key_lang in po_content and key_source in po_content[key_lang]:
            replaced_translation = po_content[key_lang][key_source]
        else:
            fuzz_match_ratio = [fuzz.ratio(sanitize(k), key_source) for k in po_content[key_lang].keys()]
            fuzz_max_ratio = max(fuzz_match_ratio)
            fuzz_match_key = list(po_content[key_lang].keys())[fuzz_match_ratio.index(fuzz_max_ratio)]
            if fuzz_max_ratio > 90:
                replaced_translation = po_content[key_lang][fuzz_match_key]
                tuvs[0].find("seg").text = sanitize(fuzz_match_key)
            else:
                print(f"[{key_lang}] {key_source} == {fuzz_match_key} [{fuzz_max_ratio}]")
                continue
        tuvs[1].find("seg").text = sanitize(replaced_translation)
        # if the tvus[1].find("seg").text is a single ", remove the tu element as whole (since this is an untranslated string)
        if tuvs[1].find("seg").text == "\"":
            to_be_removed.append(tu)

    print(f"Removed {len(to_be_removed)} elements")
    body = root.find("body")
    for tu in to_be_removed:
        body.remove(tu)
    fixed_root = ET.ElementTree(root)
    fixed_root.write(tmx_target_path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix a corrupted Translation memory from existing po files")
    parser.add_argument("tmx_source_path", type=Path, help="Path to the source TMX file")
    parser.add_argument("tmx_target_path", type=Path, help="Path to the target TMX file")
    parser.add_argument("i18n_path", type=Path, help="Path to the i18n folder")
    args = parser.parse_args()
    main(args.tmx_source_path, args.tmx_target_path, args.i18n_path)
