"""member_store.py - read and write a club's sailors, <club>Sail.xml (RMBCSail.xml, say).

The file is in the club's folder (see model/club.py), one <sail> per boat:

    <sails>
      <sail sailnumber="   01" boatclass="VICTORIA" forename="Polly" surname="Breeze" tag="PB" />
      <sail sailnumber="   02" boatclass="DF95" forename="Sam" surname="Tiller" tag="ST" />
      ...
    </sails>

tag tells sailors apart when sail numbers clash across classes; left out, it is the initials.
Files from before version 1.05 also give each sailor a club="..."; it is ignored, as every
sailor in the file is the club's.
"""

from __future__ import annotations

# Files are only read through xml_file.parse_xml, which refuses XML bombs.
import xml.etree.ElementTree as ET  # nosec B405
from pathlib import Path

from ..model.member_list import MemberList
from ..model.sailor import Sailor
from .errors import StorageError
from .xml_file import parse_xml, write_xml

_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<!-- Club sailors. Add one <sail> for each boat; race results can only use these sail numbers.

  <sail sailnumber="   01" boatclass="DF95" forename="John" surname="Smith" />
-->
<sails>
</sails>
"""


def members_from_xml(root: ET.Element, path: Path | None = None) -> MemberList:
    name = path.name if path is not None else "The sailors file"
    if root.tag != "sails":
        raise StorageError(f"{name} should contain a <sails> element.")
    sailors = []
    for number, el in enumerate(root.findall("sail"), start=1):
        sailor = Sailor(el.get("sailnumber", ""), el.get("boatclass", "").strip(),
                        el.get("forename", "").strip(), el.get("surname", "").strip(),
                        el.get("tag", ""))
        problem = sailor.problem()
        if problem:
            raise StorageError(f"{name}, sail {number}: {problem}")
        sailors.append(sailor)
    return MemberList(sailors, path)


def members_to_xml(members: MemberList) -> ET.Element:
    root = ET.Element("sails")
    for s in members.sailors:
        ET.SubElement(root, "sail", {"sailnumber": s.sail_number, "boatclass": s.boat_class,
                                     "forename": s.forename, "surname": s.surname, "tag": s.tag})
    return root


def save_members(members: MemberList, path) -> None:
    """Write the sailors to path, keeping the previous version as <name>.bak.

    Like competition files, it is written beside the old file and then swapped into place.
    Raises StorageError.
    """
    write_xml(members_to_xml(members), Path(path), make_folder=True)


def load_members(path) -> MemberList:
    """Read the sailors from path, creating an empty file if it is missing. Raises StorageError."""
    path = Path(path)
    try:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(_TEMPLATE, encoding="utf-8")
        root = parse_xml(path)
    except ET.ParseError as exc:
        raise StorageError(f"{path} is not valid XML: {exc}") from exc
    except OSError as exc:
        raise StorageError(f"Could not read {path}: {exc.strerror or exc}") from exc
    return members_from_xml(root, path)
