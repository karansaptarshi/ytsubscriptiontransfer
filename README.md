# YouTube Subscription Copier

A Python script to copy YouTube subscriptions from one account to another.

## Purpose

I wanted to transfer all my YouTube channel subscriptions from one Google account to another. Instead of manually subscribing to 160+ channels one by one, this script automates the process by:

1. Reading a list of YouTube channel URLs from a CSV/Excel file
2. Opening a browser and letting you log into your new YouTube account
3. Automatically visiting each channel and clicking the Subscribe button

## How to Export Your Subscriptions

1. Go to [Google Takeout](https://takeout.google.com/)
2. Deselect all, then select only "YouTube and YouTube Music"
3. Click "All YouTube data included" and select only "subscriptions"
4. Export and download the file
5. Extract the CSV file containing your subscription URLs

## Setup

```bash
# Install dependencies
pip3 install -r requirements.txt
```

## Usage

```bash
# Run with your CSV file
/opt/homebrew/bin/python3.11 subscribe_channels.py your_channels.csv
```

Or if your Python path is set up:
```bash
python3 subscribe_channels.py your_channels.csv
```

## What Happens

1. A Chrome browser window opens
2. You have 60 seconds to log into your YouTube/Google account
3. The script automatically visits each channel and subscribes
4. Progress is shown in the terminal
5. A summary is displayed at the end

## File Format

The CSV/Excel file should have YouTube channel URLs in the first column:

```
Channel URL
https://www.youtube.com/@MrBeast
https://www.youtube.com/@mkbhd
https://www.youtube.com/channel/UC...
```

## Requirements

- Python 3.9+
- Google Chrome browser
- Dependencies in `requirements.txt`:
  - pandas
  - openpyxl
  - selenium

## Notes

- You must be logged into YouTube for subscriptions to work
- The script includes delays between subscriptions to avoid rate limiting
- Already-subscribed channels are automatically skipped

