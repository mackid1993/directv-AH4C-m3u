#!/usr/bin/env python3
"""Generate a DirecTV deep link M3U file for ah4c from a curl command."""

import json
import shlex
import subprocess
import sys
import urllib.request


def parse_curl(curl_text):
    """Parse a curl command string into URL and headers."""
    curl_text = curl_text.replace("\\\n", " ").replace("\\\r\n", " ")
    parts = shlex.split(curl_text)

    url = None
    headers = {}
    i = 0
    while i < len(parts):
        p = parts[i]
        if p == "curl":
            i += 1
            continue
        if p in ("-H", "--header") and i + 1 < len(parts):
            i += 1
            key, _, val = parts[i].partition(":")
            headers[key.strip()] = val.strip()
        elif not p.startswith("-"):
            url = p
        i += 1

    if not url:
        print("Error: could not find URL in curl command.")
        sys.exit(1)

    return url, headers


def fetch_channels(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["channelInfoList"]


def assign_channel_numbers(channels):
    """Assign display numbers, appending .1 .2 .3 for overflow channels.

    Within a shared channel number, the main channel keeps the base number.
    Channels with ALT/Alternate/Overflow in the name sort after, then by
    name length (shorter first), then alphabetically.
    """
    import re
    from itertools import groupby

    alt_pattern = re.compile(r"ALT-|ALT |Alternate|Overflow", re.IGNORECASE)

    grouped = {}
    for ch in channels:
        grouped.setdefault(ch["channelNumber"], []).append(ch)

    result = []
    for num in sorted(grouped, key=lambda n: int(n)):
        group = grouped[num]
        if len(group) == 1:
            result.append((num, group[0]))
        else:
            group.sort(key=lambda c: (
                1 if alt_pattern.search(c["channelName"]) else 0,
                len(c["channelName"]),
                c["channelName"],
            ))
            for idx, ch in enumerate(group):
                display_num = num if idx == 0 else f"{num}.{idx}"
                result.append((display_num, ch))

    return result


def generate_m3u_osprey(channels):
    """Osprey format: uses channelName in URL."""
    lines = ["#EXTM3U", ""]
    for display_num, ch in assign_channel_numbers(channels):
        ch_name = ch["channelName"]
        res_id = ch["resourceId"]
        ext_id = ch.get("externalListingId", "")
        url_name = ch_name.replace(" ", "-")

        lines.append(
            f'#EXTINF:-1 channel-id="{display_num}" channel-number="{display_num}" '
            f'tvc-guide-stationid="{ext_id}",{ch_name}'
        )
        lines.append(
            f"http://{{{{ .IPADDRESS }}}}/play/tuner/{url_name}~{res_id}"
        )
        lines.append("")

    return "\n".join(lines)


def generate_m3u_dtvapp(channels):
    """DirecTV app format: uses callSign in URL, includes tvg-group/tvg-logo."""
    lines = ["#EXTM3U", ""]
    for display_num, ch in assign_channel_numbers(channels):
        ch_name = ch["channelName"]
        call_sign = ch["callSign"]
        res_id = ch["resourceId"]
        ext_id = ch.get("externalListingId", "")

        lines.append(
            f'#EXTINF:-1 channel-id="{display_num}" channel-number="{display_num}" '
            f'tvc-guide-stationid="{ext_id}" tvg-group="" tvg-logo="",{ch_name}'
        )
        lines.append(
            f"http://{{{{ .IPADDRESS }}}}/play/tuner/{call_sign}~{res_id}"
        )
        lines.append("")

    return "\n".join(lines)


def get_curl_from_clipboard():
    """Get curl command from clipboard."""
    try:
        result = subprocess.run(
            ["pbpaste"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and "curl" in result.stdout:
            return result.stdout
    except FileNotFoundError:
        pass

    try:
        result = subprocess.run(
            ["powershell", "-command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and "curl" in result.stdout:
            return result.stdout
    except FileNotFoundError:
        pass

    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and "curl" in result.stdout:
            return result.stdout
    except FileNotFoundError:
        pass

    return None


def main():
    print("Select format:")
    print("  1) Osprey")
    print("  2) DirecTV App")
    choice = input("Enter 1 or 2: ").strip()
    if choice not in ("1", "2"):
        print("Invalid choice, exiting.")
        sys.exit(1)

    output_file = input("Enter output filename: ").strip()
    if not output_file:
        print("No filename provided, exiting.")
        sys.exit(1)
    if output_file.endswith(".m3u"):
        output_file = output_file[:-4]
    output_file += ".m3u"

    print("\nCopy your curl command to clipboard, then press Enter...")
    input()

    curl_text = get_curl_from_clipboard()
    if not curl_text:
        print("Error: no curl command found in clipboard.")
        sys.exit(1)

    print("Got curl from clipboard.")
    url, headers = parse_curl(curl_text)

    print("Fetching channel data...")
    channels = fetch_channels(url, headers)
    channels.sort(key=lambda ch: int(ch["channelNumber"]))
    print(f"Got {len(channels)} channels")

    if choice == "1":
        m3u = generate_m3u_osprey(channels)
    else:
        m3u = generate_m3u_dtvapp(channels)

    with open(output_file, "w") as f:
        f.write(m3u)

    print(f"Written to {output_file}")


if __name__ == "__main__":
    main()
