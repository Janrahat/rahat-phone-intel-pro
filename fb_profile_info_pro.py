#!/usr/bin/env python3
# FB PROFILE INFO PRO — safe public Facebook link analyzer for Termux
# This tool analyzes a Facebook profile URL and its visible URL structure.
# It does NOT bypass login, scrape private data, or reveal hidden profile details.

import json
import os
import re
import webbrowser
from datetime import datetime
from urllib.parse import urlparse, parse_qs, unquote

try:
    from colorama import Fore, Style, init
except ImportError:
    print("Missing package. Install with: pip install colorama")
    raise SystemExit(1)

init(autoreset=True)
CYAN, GREEN, YELLOW = Fore.CYAN, Fore.GREEN, Fore.YELLOW
RED, MAGENTA, WHITE = Fore.RED, Fore.MAGENTA, Fore.WHITE
BRIGHT, RESET = Style.BRIGHT, Style.RESET_ALL

APP = "FB PROFILE INFO PRO"
REPORT_DIR = "fb_reports"
FB_HOSTS = {"facebook.com", "www.facebook.com", "m.facebook.com", "mbasic.facebook.com", "web.facebook.com"}

def banner():
    os.system("clear" if os.name != "nt" else "cls")
    print(CYAN + BRIGHT + r"""
╔══════════════════════════════════════════════════════╗
║                 FB PROFILE INFO PRO                 ║
║          Colorful Facebook Link Analyzer            ║
╚══════════════════════════════════════════════════════╝
""" + RESET)
    print(YELLOW + "Public-link analysis only. No private data, password access,")
    print("hidden email/phone, private posts, or live location retrieval.\n")

def normalize_fb_url(raw):
    raw = raw.strip()
    if not raw:
        raise ValueError("No link entered.")
    if not re.match(r"^https?://", raw, re.I):
        raw = "https://" + raw
    p = urlparse(raw)
    host = (p.hostname or "").lower()
    if host not in FB_HOSTS and not host.endswith(".facebook.com"):
        raise ValueError("This does not look like an official facebook.com URL.")
    if p.scheme not in ("http", "https"):
        raise ValueError("Unsupported URL scheme.")
    # Do not accept lookalike hosts such as facebook.com.example.org.
    if not (host == "facebook.com" or host.endswith(".facebook.com")):
        raise ValueError("Not an official Facebook domain.")
    path = unquote(p.path or "/")
    clean = "https://www.facebook.com" + path
    if p.query:
        # Keep only common profile routing parameters that may identify the profile.
        q = parse_qs(p.query)
        kept = {}
        for k in ("id", "profile.php"):
            if k in q:
                kept[k] = q[k]
        if kept:
            from urllib.parse import urlencode
            clean += "?" + urlencode(kept, doseq=True)
    return clean, p, path

def analyze_link(raw):
    clean, parsed, path = normalize_fb_url(raw)
    query = parse_qs(parsed.query)
    parts = [x for x in path.split("/") if x]
    profile_id = None
    username = None
    profile_kind = "Profile/page link (type not confirmed)"

    if parts and parts[0].lower() == "profile.php":
        profile_id = (query.get("id") or [None])[0]
        profile_kind = "Numeric profile.php link"
    elif "id" in query and query["id"]:
        profile_id = query["id"][0]
        profile_kind = "Link with numeric ID parameter"
    elif parts:
        first = parts[0]
        reserved = {
            "groups", "pages", "events", "watch", "marketplace", "reel",
            "reels", "stories", "photo.php", "photos", "videos", "posts",
            "share", "login", "help", "settings", "gaming", "fundraisers"
        }
        if first.lower() not in reserved:
            username = first
            profile_kind = "Username/custom-path style link (not verified)"
        else:
            profile_kind = "Facebook content or section link (not necessarily a profile)"

    info = {
        "tool": APP,
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "input_url": raw.strip(),
        "normalized_url": clean,
        "official_facebook_domain": True,
        "link_type_guess": profile_kind,
        "username_or_first_path_segment": username or "Not found in URL",
        "numeric_profile_id_in_url": profile_id or "Not present in URL",
        "url_path": path or "/",
        "query_parameter_names": sorted(query.keys()),
        "limitations": [
            "This tool inspects the URL only; it does not confirm the account exists.",
            "It cannot retrieve private profile data or reveal hidden phone/email.",
            "A username/path segment may be a page or content route, not a personal profile.",
            "Facebook may redirect, require login, or change profile URL formats."
        ]
    }
    return info

def show_report(info):
    print("\n" + MAGENTA + BRIGHT + "════════════ LINK ANALYSIS REPORT ════════════")
    rows = [
        ("Normalized link", info["normalized_url"]),
        ("Official Facebook domain", "YES" if info["official_facebook_domain"] else "NO"),
        ("Link type", info["link_type_guess"]),
        ("Username/path", info["username_or_first_path_segment"]),
        ("Numeric profile ID", info["numeric_profile_id_in_url"]),
        ("URL path", info["url_path"]),
        ("Query parameter names", ", ".join(info["query_parameter_names"]) or "None"),
    ]
    for label, value in rows:
        print(f"{CYAN}{label:<26}{WHITE}: {GREEN}{value}")
    print(YELLOW + "\nImportant: these are URL-derived details, not verified account information.")
    print(YELLOW + "For full public profile details, open the profile in Facebook and view only what")
    print("the account owner has made public. This tool does not bypass privacy settings.")

def save_report(info):
    os.makedirs(REPORT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(REPORT_DIR, f"fb_link_report_{stamp}")
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    with open(base + ".txt", "w", encoding="utf-8") as f:
        f.write(APP + "\n" + "=" * 48 + "\n")
        for k, v in info.items():
            f.write(f"{k}: {v}\n")
    print(GREEN + f"Saved report files:\n  {base}.txt\n  {base}.json")

def main():
    while True:
        banner()
        print(GREEN + BRIGHT + " [1] Analyze a Facebook profile/link")
        print(GREEN + " [2] Open a Facebook link in browser")
        print(GREEN + " [3] About / limitations")
        print(RED + " [0] Exit\n")
        choice = input(CYAN + "Select option > " + WHITE).strip()

        if choice == "1":
            raw = input("\nPaste Facebook URL > ").strip()
            try:
                info = analyze_link(raw)
                show_report(info)
                if input("\nSave TXT + JSON report? [y/N] > ").strip().lower() == "y":
                    save_report(info)
            except ValueError as e:
                print(RED + f"Error: {e}")
            input("\nPress Enter to return to menu...")
        elif choice == "2":
            raw = input("\nPaste Facebook URL > ").strip()
            try:
                clean, _, _ = normalize_fb_url(raw)
                print(GREEN + "Opening: " + clean)
                opened = webbrowser.open(clean)
                if not opened:
                    print(YELLOW + "If the browser did not open, copy this link: " + clean)
            except ValueError as e:
                print(RED + f"Error: {e}")
            input("\nPress Enter to return to menu...")
        elif choice == "3":
            print("\nThis is a public URL analyzer, not a Facebook account database.")
            print("It can extract URL path/username-like segment and an ID if included in the URL.")
            print("It cannot reveal private posts, hidden phone/email, passwords, IP address,")
            print("messages, friends-only data, or someone's live location.")
            input("\nPress Enter to return to menu...")
        elif choice == "0":
            print(GREEN + "Goodbye!")
            break
        else:
            print(RED + "Invalid option.")
            input("Press Enter...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + YELLOW + "Exited safely.")
