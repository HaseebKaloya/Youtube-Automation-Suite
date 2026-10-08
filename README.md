# YouTube Automation Suite

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg?style=flat-square)]()
[![API](https://img.shields.io/badge/YouTube%20API-v3-red.svg?style=flat-square&logo=youtube&logoColor=white)](https://developers.google.com/youtube/v3)

A fast, reliable desktop and command-line automation suite for managing YouTube interactions in bulk using the official YouTube Data API v3 with OAuth 2.0 authentication.

---

## Key Capabilities

- **Dual Interfaces**: Choose between a dark-mode graphical desktop application (built with CustomTkinter) or a lightweight, scriptable command-line interface.
- **Bulk Operations**: Automate video likes, channel subscriptions, and top-level comment posting from text input files.
- **Smart Identifiers**: Automatically resolves standard video URLs, short URLs (`youtu.be`), channel IDs (`UC...`), and creator handles (`@username`).
- **Quota & Rate-Limit Protection**: Built-in exponential backoff, customizable execution delays, and random jitter to stay safely within YouTube API limits.
- **Deduplication & State Persistence**: Tracks previously processed items in local JSON state files to prevent repeated likes or duplicate comments across sessions.
- **Audit Logging**: Keeps structured CSV records of every executed request along with timestamps and API response statuses.

---

## Prerequisites

1. **Python 3.8+** installed on your system.
2. A **Google Cloud Project** with the **YouTube Data API v3** enabled.
3. OAuth 2.0 Desktop Client credentials downloaded as `credentials.json` placed in the project root directory.

> **Note**: For a step-by-step walkthrough on setting up your Google Cloud Console credentials and OAuth consent screen, visit the [Project Wiki](https://github.com/HaseebKaloya/Youtube-Automation-Suite/wiki).

---

## Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/HaseebKaloya/Youtube-Automation-Suite.git
cd Youtube-Automation-Suite
pip install -r requirements.txt
```

---

## Usage

Place your `credentials.json` file in the repository root directory before launching.

### Graphical Interface (GUI)

Launch the desktop interface:

```bash
python -m src.youtube_automation_gui
```

*On Windows, you can also double-click `START_GUI.bat`.*

The GUI allows you to select input files, toggle desired automation actions, configure timing delays, monitor real-time execution logs, and stop tasks at any time.

### Command-Line Interface (CLI)

#### 1. Interactive Mode
Run the CLI without arguments to launch the guided interactive setup:

```bash
python -m src.youtube_automation_cli
```

*On Windows, you can also double-click `START_CLI.bat`.*

#### 2. Headless / Scripted Mode
Automate tasks directly by supplying command-line flags:

```bash
# Like videos listed in a text file
python -m src.youtube_automation_cli --action like --file examples/likes.txt

# Subscribe to channels listed in a text file
python -m src.youtube_automation_cli --action subscribe --file examples/channels.txt

# Post comments to a specific target video
python -m src.youtube_automation_cli --action comment --file examples/comments.txt --video <VIDEO_ID_OR_URL>

# Customize pacing (e.g., 5s delay with +/- 1.5s jitter)
python -m src.youtube_automation_cli --action like --file examples/likes.txt --delay 5.0 --jitter 1.5
```

---

## Input File Format

Input files are plain UTF-8 text files containing one entry per line:

- **Likes (`likes.txt`)**: Video URLs or 11-character video IDs.
  ```text
  https://www.youtube.com/watch?v=dQw4w9WgXcQ
  https://youtu.be/9bZkp7q19f0
  ```

- **Channels (`channels.txt`)**: Full channel URLs, channel IDs, or `@handles`.
  ```text
  https://www.youtube.com/@mkbhd
  UC_x5XG1OV2P6uZZ5FSM9Ttw
  ```

- **Comments (`comments.txt`)**: Comment strings, one per line.
  ```text
  Great breakdown, thanks for sharing!
  Very informative video.
  ```

Sample templates are available in the `examples/` directory.

---

## Project Structure

```text
Youtube-Automation-Suite/
├── assets/
│   └── images/                       # Project and developer visual assets
├── examples/                         # Sample input and configuration templates
│   ├── channels.txt
│   ├── comments.txt
│   ├── likes.txt
│   └── sample_config.json
├── src/
│   ├── __init__.py
│   ├── youtube_automation_cli.py     # Command-line interface
│   └── youtube_automation_gui.py     # Desktop GUI application
├── .gitignore                        # Git exclusion rules for secrets and caches
├── LICENSE                           # MIT License
├── README.md                         # Documentation
├── requirements.txt                  # Python dependencies
├── START_CLI.bat                     # Windows CLI launcher
└── START_GUI.bat                     # Windows GUI launcher
```

---

## Developer

<table>
  <tr>
    <td align="center" width="130">
      <img src="assets/images/developer_avatar.jpg" width="100" height="100" style="border-radius: 50%; object-fit: cover;" alt="Haseeb Kaloya">
    </td>
    <td>
      <strong>Haseeb Kaloya</strong><br>
      Lead Developer & Maintainer<br><br>
      Email: <a href="mailto:contact.haseebkaloya@gmail.com">contact.haseebkaloya@gmail.com</a>
    </td>
  </tr>
</table>

---

## License

This project is licensed under the [MIT License](LICENSE).
