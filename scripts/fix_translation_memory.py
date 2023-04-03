##% Script to fix a corrupted Translation memory from existing po files

import os
import re
import argparse
from pathlib import Path
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
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
    return dict(re.findall(r'[^#]msgid.?\"+\s?([\s|\S]+?)\"*?msgstr.?\"([\s|\S]+?)\"?#', content))


def main(tmx_source_path: Path, tmx_target_path: Path, i18n_path: Path):

    po_content = {}
    for file in i18n_path.rglob("cura.po"):
        print(os.path.join(i18n_path, file))
        po_content[file.relative_to(i18n_path).parts[0].replace("_", "-")] = load_existing_po(Path(os.path.join(i18n_path, file)))

    root = load_existing_xmtm(tmx_source_path)
    root_old = ET.ElementTree(root)
    root_old.write("old.tmx", encoding="utf-8", xml_declaration=True)
    for tu in root.iter("tu"):
        if "cura.pot" not in [t.text for t in tu.findall("prop") if t.attrib["type"] == "x-smartling-file"]:
            continue
        tuvs = tu.findall("tuv")
        key_source = tuvs[0].find("seg").text
        key_lang = tuvs[1].attrib["{http://www.w3.org/XML/1998/namespace}lang"]
        if key_lang in po_content and key_source in po_content[key_lang]:
            tuvs[1].find("seg").text = po_content[key_lang][key_source]
        else:
            fuzz_match_ratio = [fuzz.ratio(k, key_source) for k in po_content[key_lang].keys()]
            fuzz_max_ratio = max(fuzz_match_ratio)
            fuzz_match_key = list(po_content[key_lang].keys())[fuzz_match_ratio.index(fuzz_max_ratio)]
            if fuzz_max_ratio > 90:
                fuzz_match_po_value = po_content[key_lang][fuzz_match_key]
                tuvs[0].find("seg").text = fuzz_match_key
                tuvs[1].find("seg").text = fuzz_match_po_value
                # print(f"[{key_lang}] Fuzz match: {key_source} -> {fuzz_match_key} -> {fuzz_match_po_value} with a ratio of {fuzz_max_ratio}")
            else:
                # print(f"[{key_lang}] No match for: {key_source} -> {tuvs[1].find('seg').text} -> highest ratio: {fuzz_max_ratio}")
                print(f"[{key_lang}] {key_source} == {fuzz_match_key} [{fuzz_max_ratio}]")
    fixed_root = ET.ElementTree(root)
    fixed_root.write(tmx_target_path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix a corrupted Translation memory from existing po files")
    parser.add_argument("tmx_source_path", type=Path, help="Path to the source TMX file")
    parser.add_argument("tmx_target_path", type=Path, help="Path to the target TMX file")
    parser.add_argument("i18n_path", type=Path, help="Path to the i18n folder")
    args = parser.parse_args()
    main(args.tmx_source_path, args.tmx_target_path, args.i18n_path)
