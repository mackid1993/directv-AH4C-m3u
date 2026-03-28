# DirecTV M3U Generator for ah4c

Generates an M3U channel lineup from the DirecTV Stream API for use with [ah4c](https://github.com/sullrich/ah4c)

## Requirements

- Python 3
- A valid DirecTV Stream bearer token (from a browser session)

## Usage

1. Log into [stream.directv.com](https://stream.directv.com) in your browser
2. Open DevTools > Network, find the `allchannels` API call, and **Copy as cURL**
3. Run the script:

```bash
python3 generate_directv_m3u.py
```

4. Select your format:
   - **1) Osprey** — uses `channelName` in the URL (for Osprey devices)
   - **2) DirecTV App** — uses `callSign` in the URL (for the standard DirecTV app)
5. Enter an output filename (`.m3u` is added automatically)
6. Copy the curl command to your clipboard and press Enter

The script reads the curl from your clipboard automatically (macOS, Windows, and Linux supported).

## Overflow Channels

When multiple channels share the same number (e.g. MSG alternates), the main channel keeps the base number and overflows get `.1`, `.2`, `.3`, etc. ALT/Alternate/Overflow channels always sort after the primary.
