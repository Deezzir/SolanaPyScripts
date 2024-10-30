import argparse
import random
import xml.etree.ElementTree as ET
from xml.dom import minidom


def generate_profiles(num_profiles) -> ET.Element:
    profiles = ET.Element("profiles")

    for index in range(1, num_profiles + 1):
        profile = ET.SubElement(profiles, "profile")

        profile_name = ET.SubElement(profile, "profile_name")
        profile_name.text = f"Profile {index}"

        amount = ET.SubElement(profile, "amount")
        amount.text = f"{random.uniform(0.8, 2.0):.2f}"

        slippage = ET.SubElement(profile, "slippage")
        slippage.text = "100000"

        priority = ET.SubElement(profile, "priority")
        priority.text = f"{random.uniform(0.01, 0.4):.2f}"

    return profiles


def pretty_print_xml(elem) -> str:
    rough_string = ET.tostring(elem, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an XML file with profile records."
    )
    parser.add_argument(
        "num_records",
        type=int,
        nargs="?",
        default=10,
        help="Number of profile records to generate (default: 10)",
    )
    args = parser.parse_args()

    profiles = generate_profiles(args.num_records)
    pretty_xml = pretty_print_xml(profiles)

    with open("profiles.xml", "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    print(f"Generated profiles.xml with {args.num_records} profiles")


if __name__ == "__main__":
    main()
