#!/usr/bin/env python3

"""Simple script to display all hardware info collected by the client."""

from pprint import pprint

import hardware_info


def main():
    """Collect and display hardware info."""
    print("\n=== Hardware Info Collection Test ===\n")

    # Get all hardware info
    print("Getting hardware info...")
    try:
        info = hardware_info.get_hardware_info()
        print("\nRaw hardware info:")
        pprint(info)
    except Exception as e:
        print(f"Error getting hardware info: {e}")

    # Get individual components
    components = [
        ("CPU Info", hardware_info.get_cpu_info),
        ("RAM Info", hardware_info.get_ram_info),
        ("GPU Info", hardware_info.get_gpus_info),
        ("NPU Info", hardware_info.get_npu_info),
        ("Firmware Info", hardware_info.get_firmware_info),
    ]

    for name, func in components:
        print(f"\n=== {name} ===")
        try:
            component_info = func()
            pprint(component_info)
        except Exception as e:
            print(f"Error getting {name}: {e}")


if __name__ == "__main__":
    main()
