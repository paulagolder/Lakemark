"""boat_class_store.py - read and write a club's boat classes, <club>Classes.xml.

The file is in the club's folder (RMBCClasses.xml, say; see model/club.py), one <boatclass>
per class:

    <classes>
      <boatclass key="df65" fullname="DF65" cypher="65" symbol="#" />
      <boatclass key="rg65" fullname="RG65" cypher="rg" symbol="$" />
      <boatclass key="df95" fullname="DF95" cypher="95" symbol="@" />
      <boatclass key="victoria" fullname="Victoria" cypher="Va" symbol="*" />
    </classes>

If the file is missing it is created with these four classes.
"""

from __future__ import annotations

# Files are only read through xml_file.parse_xml, which refuses XML bombs.
import xml.etree.ElementTree as ET  # nosec B405
from pathlib import Path

from ..model.boat_class import DEFAULT_BOAT_CLASSES, BoatClass, BoatClassList
from .errors import StorageError
from .xml_file import parse_xml, write_xml


def boat_classes_from_xml(root: ET.Element, name: str = "The classes file") -> BoatClassList:
    if root.tag != "classes":
        raise StorageError(f"{name} should contain a <classes> element.")
    classes = BoatClassList()
    for number, el in enumerate(root.findall("boatclass"), start=1):
        boat_class = BoatClass(el.get("key", "").strip(), el.get("fullname", "").strip(),
                               el.get("cypher", "").strip(), el.get("symbol", "").strip())
        try:
            classes.add(boat_class)
        except ValueError as exc:
            raise StorageError(f"{name}, class {number}: {exc}") from exc
    return classes


def boat_classes_to_xml(classes: BoatClassList) -> ET.Element:
    root = ET.Element("classes")
    for c in classes.classes:
        ET.SubElement(root, "boatclass", {"key": c.key, "fullname": c.fullname,
                                          "cypher": c.cypher, "symbol": c.symbol})
    return root


def save_boat_classes(classes: BoatClassList, path) -> None:
    """Write the classes to path, keeping the previous version as <name>.bak.

    Raises StorageError.
    """
    write_xml(boat_classes_to_xml(classes), Path(path), make_folder=True)


def load_boat_classes(path) -> BoatClassList:
    """Read the classes from path, creating it with the default classes if it is missing.

    Raises StorageError.
    """
    path = Path(path)
    if not path.exists():
        save_boat_classes(BoatClassList(DEFAULT_BOAT_CLASSES), path)
    try:
        root = parse_xml(path)
    except ET.ParseError as exc:
        raise StorageError(f"{path} is not valid XML: {exc}") from exc
    except OSError as exc:
        raise StorageError(f"Could not read {path}: {exc.strerror or exc}") from exc
    return boat_classes_from_xml(root, path.name)


def boat_classes_or_defaults(path) -> BoatClassList:
    """The classes in the file. Never raises: if it cannot be read (or is empty), the
    default classes."""
    try:
        classes = load_boat_classes(path)
    except StorageError:
        classes = BoatClassList()
    return classes if len(classes) else BoatClassList(DEFAULT_BOAT_CLASSES)
