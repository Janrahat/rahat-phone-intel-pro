#!/usr/bin/env python3
# RAHAT PHONE INTEL PRO — public phone-number metadata only
# For Termux: pip install phonenumbers colorama

import json
import os
import re
from datetime import datetime

try:
    import phonenumbers
    from phonenumbers import geocoder, carrier, timezone
    from phonenumbers.phonenumberutil import number_type, PhoneNumberType
    from colorama import Fore, Style, init
except ImportError:
    print("Missing packages. Run: pip install phonenumbers colorama")
    raise SystemExit(1)

init(autoreset=True)

C = {
    "cyan": Fore.CYAN, "green": Fore.GREEN, "yellow": Fore.YELLOW,
    "red": Fore.RED, "magenta": Fore.MAGENTA, "blue": Fore.BLUE,
    "white": Fore.WHITE, "bright": Style.BRIGHT, "reset": Style.RESET_ALL
}

APP = "RAHAT PHONE INTEL PRO"
REPORT_DIR = "phone_reports"

def banner():
    os.system("clear" if os.name != "nt" else "cls")
    print(C["cyan"] + C["bright"] + r"""
╔══════════════════════════════════════════════════════╗
║              RAHAT PHONE INTEL PRO                  ║
║        Public Number Metadata • Termux Edition      ║
╚══════════════════════════════════════════════════════╝
""" + C["reset"])
    print(C["yellow"] + "  Note: phone numbers do NOT reveal live GPS or a home address.")
    print(C["yellow"] + "  Use only for lawful, consent-based checks.\n")

def label_type(n):
    t = number_type(n)
    names = {
        PhoneNumberType.MOBILE: "Mobile",
        PhoneNumberType.FIXED_LINE: "Fixed line",
        PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed line or mobile",
        PhoneNumberType.TOLL_FREE: "Toll-free",
        PhoneNumberType.PREMIUM_RATE: "Premium-rate",
        PhoneNumberType.SHARED_COST: "Shared-cost",
        PhoneNumberType.VOIP: "VoIP",
        PhoneNumberType.PERSONAL_NUMBER: "Personal number",
        PhoneNumberType.PAGER: "Pager",
        PhoneNumberType.UAN: "UAN",
        PhoneNumberType.VOICEMAIL: "Voicemail",
        PhoneNumberType.UNKNOWN: "Unknown",
    }
    return names.get(t, "Unknown")

def inspect_number(raw, region=None):
    raw = raw.strip()
    if not raw:
        print(C["red"] + "No number entered.")
        return

    try:
        parsed = phonenumbers.parse(raw, region.upper() if region else None)
    except phonenumbers.NumberParseException as e:
        print(C["red"] + f"Could not parse number: {e}")
        print(C["yellow"] + "Tip: enter international format, e.g. +9665XXXXXXXX")
        return

    possible = phonenumbers.is_possible_number(parsed)
    valid = phonenumbers.is_valid_number(parsed)
    info = {
        "tool": APP,
        "checked_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "input": raw,
        "international_format": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
        "e164_format": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
        "national_format": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
        "country_calling_code": "+" + str(parsed.country_code),
        "country_or_region": geocoder.country_name_for_number(parsed, "en") or "Not available",
        "number_region_description": geocoder.description_for_number(parsed, "en") or "Not available",
        "carrier_label_if_available": carrier.name_for_number(parsed, "en") or "Not available",
        "number_type": label_type(parsed),
        "time_zones": list(timezone.time_zones_for_number(parsed)),
        "possible_number": bool(possible),
        "valid_number_by_numbering_plan": bool(valid),
        "note": "Metadata only; not live GPS, subscriber identity, or exact address."
    }

    print("\n" + C["magenta"] + C["bright"] + "──── NUMBER INTELLIGENCE REPORT ────")
    rows = [
        ("International", info["international_format"]),
        ("E.164", info["e164_format"]),
        ("National", info["national_format"]),
        ("Calling code", info["country_calling_code"]),
        ("Country/region", info["country_or_region"]),
        ("Region description", info["number_region_description"]),
        ("Carrier label", info["carrier_label_if_available"]),
        ("Number type", info["number_type"]),
        ("Time zone(s)", ", ".join(info["time_zones"]) or "Not available"),
        ("Possible", "YES" if possible else "NO"),
        ("Valid numbering-plan format", "YES" if valid else "NO"),
    ]
    for k, v in rows:
        color = C["green"] if str(v) in ("YES",) else C["red"] if str(v) == "NO" else C["white"]
        print(f"{C['cyan']}{k:<29}{C['white']}: {color}{v}")
    print(C["yellow"] + "\nImportant: country/region and carrier labels can be approximate or unavailable.")
    print(C["yellow"] + "They cannot identify a person's live location or prove who owns the number.")

    save = input("\nSave report to TXT and JSON? [y/N]: ").strip().lower()
    if save == "y":
        os.makedirs(REPORT_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = re.sub(r"[^0-9A-Za-z+-]", "_", info["e164_format"])
        base = os.path.join(REPORT_DIR, f"{safe}_{stamp}")
        with open(base + ".json", "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        with open(base + ".txt", "w", encoding="utf-8") as f:
            f.write(APP + "\n" + "=" * 48 + "\n")
            for k, v in info.items():
                f.write(f"{k}: {v}\n")
        print(C["green"] + f"Saved: {base}.txt and {base}.json")

def main():
    while True:
        banner()
        print(C["green"] + C["bright"] + " [1] Check phone-number metadata")
        print(C["green"] + " [2] Help / limitations")
        print(C["red"] + " [0] Exit\n")
        choice = input(C["cyan"] + "Select option > " + C["white"]).strip()
        if choice == "1":
            raw = input("\nEnter phone number (prefer +countrycode format): ").strip()
            region = None
            if not raw.startswith("+"):
                region = input("Two-letter region if number has no +country code (e.g. SA, PK), blank to cancel: ").strip() or None
            inspect_number(raw, region)
            input("\nPress Enter to return to menu...")
        elif choice == "2":
            print("\nThis tool checks public numbering-plan metadata using the phonenumbers library.")
            print("It may show country, approximate numbering region, carrier label, type, and time zones.")
            print("It cannot retrieve live GPS, precise location, name, home address, WhatsApp data,")
            print("call logs, or private subscriber records from a phone number.")
            input("\nPress Enter to return to menu...")
        elif choice == "0":
            print(C["green"] + "Goodbye.")
            break
        else:
            print(C["red"] + "Invalid option.")
            input("Press Enter...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + C["yellow"] + "Exited safely.")
