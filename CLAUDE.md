# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AzurLaneAutoScript (ALAS) is a Python automation bot for the mobile game Azur Lane. It connects to an Android emulator (or physical device) via ADB, takes screenshots, performs OCR and template matching, and simulates touch input to automate game tasks like daily rewards, commissions, combat, events, and Operation Siren.

This repo (Heipen/AzurLaneAutoScript) is a fork of [LmeSzinc/AzurLaneAutoScript](https://github.com/LmeSzinc/AzurLaneAutoScript) with additional features: screenshot display, dashboard, Operation Siren zone 1 statistics with XP detection, and island planning. It auto-syncs with the upstream via a GitHub Actions workflow.

## Tech Stack

- **Python 3.7+** primary language
- **ADB/uiautomator2** for device connection and touch simulation
- **OpenCV** (cv2) for image template matching
- **cnocr** for Chinese OCR
- **uvicorn + PyWebIO** for the web UI backend
- **Vue 3 + Electron** for the desktop GUI (`webapp/` sub-project)
- **Node.js 14+** for the webapp build system

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `alas.py` | Main entry point - task scheduler and runner (`AzurLaneAutoScript` class) |
| `gui.py` | Web UI launcher (uvicorn server with PyWebIO) |
| `module/` | Core logic modules - each subdirectory is a game feature |
| `module/base/` | Foundational utilities: button handling, template matching, decorators, retry logic |
| `module/device/` | Device connection, screenshot capture, input simulation (ADB-based) |
| `module/config/` | Configuration system - JSON/YAML-based config management |
| `module/handler/` | Game handlers: login, auto search, enemy detection, fast forward |
| `module/campaign/` | Campaign (battle) execution logic |
| `module/ui/` | UI navigation: page detection, button routing, navbar |
| `module/os/` | Operation Siren (大世界) - map, camera, globe, fleet management |
| `module/os_combat/` | Operation Siren combat logic |
| `module/os_handler/` | Operation Siren event handlers |
| `module/os_ash/` | Operation Siren portal/ash system |
| `module/os_shop/` | Operation Siren shop |
| `campaign/` | Event/map data files - each event has its own subdirectory with YAML map definitions |
| `assets/` | Template images for UI recognition, organized by server (cn/en/jp/tw) and feature |
| `config/` | Config templates (`template.json`, `deploy.template.yaml`, etc.) |
| `deploy/` | Installation scripts, Docker setup, platform-specific deploy (AidLux, Windows) |
| `webapp/` | Electron + Vue 3 desktop application |
| `dev_tools/` | Development utilities: map extractor, campaign swipe tool, item statistics |
| `tools/` | Diagnostic scripts |
| `bin/` | Binary tools: DroidCast, scrcpy, ascreencap, MaaTouch, cnocr models |
| `submodule/` | External bridges: AlasFpyBridge, AlasMaaBridge |

## Running the Project

### Install dependencies

```bash
pip install -r requirements.txt
```

### Start the web UI

```bash
python gui.py
```

This starts a uvicorn server (default port 22267) serving the PyWebIO interface. Access via browser at `http://localhost:22267`.

### Run a specific task

Tasks are invoked through `alas.py`'s `AzurLaneAutoScript` class. Common task methods: `research`, `commission`, `tactical`, `dorm`, `meowfficer`, `guild`, `reward`, `awaken`, `shop_frequent`, etc. Each task method instantiates a handler from the corresponding `module/` subdirectory and calls its `run()` method.

### Build the Electron desktop app

```bash
cd webapp
npm install
npm run build
npm run compile
```

### Docker

```bash
docker compose build
docker compose up
```

### Development tools

- `python -m deploy.installer` - Run the ALAS installer
- `python dev_tools/map_extractor.py` - Extract map data from screenshots
- `python dev_tools/campaign_swipe.py` - Campaign swipe testing tool
- `python dev_tools/item_statistics.py` - Item statistics extraction
- `python -m module.config.config_updater` - Regenerate config files from YAML definitions in `module/config/argument/`

## Architecture

### Core Flow

1. `gui.py` starts the web server and manages config instances
2. `alas.py` (`AzurLaneAutoScript`) is the task runner - it loads config, initializes device, and dispatches to task handlers
3. Each task handler (e.g., `module/research/research.py`) inherits from base classes and uses the device to screenshot, detect UI elements, and send input
4. The `module/device/device.py` class wraps ADB/uiautomator2 for screenshot capture and touch input
5. UI navigation (`module/ui/ui.py`) handles page detection and routing between game screens
6. Template matching (`module/base/template.py`) and OCR (`module/ocr/`) recognize game UI elements

### Config System

- `module/config/argument/` contains YAML files that define the config schema and GUI layout:
  - `argument.yaml` - argument group definitions (types, defaults, options)
  - `task.yaml` - task-to-argument-group mappings
  - `override.yaml` - overrides/locks specific values per task (e.g. CoalitionSp hard-codes Mode='sp')
  - `default.yaml` - default values
  - `gui.yaml` - GUI-specific settings
- `module/config/argument/args.json` - fully merged argument definitions (auto-generated, **DO NOT manually edit**)
- `module/config/config_generated.py` - Python constants for argument groups (auto-generated, **DO NOT manually edit**)
- `module/config/config.py` (`AzurLaneConfig`) loads user config and merges with args.json defaults
- `module/config/config_updater.py` regenerates args.json, config_generated.py, and menu.json from the argument YAML files
- To add/modify a config option: edit the YAML files in `module/config/argument/`, then run `python -m module.config.config_updater`. **Never manually edit args.json or config_generated.py.**
- `config/template.json` is a legacy file, no longer the primary source of config schema
- User configs stored in `config/{config_name}.json`

### Exception Hierarchy

Defined in `module/exception.py`:
- `CampaignEnd`, `OilExhausted` - normal campaign termination
- `MapDetectionError`, `MapWalkError`, `MapEnemyMoved` - map navigation errors
- `GameStuckError`, `GameBugError`, `GameTooManyClickError` - game state errors (trigger restart)
- `GameNotRunningError`, `GamePageUnknownError` - connectivity/page errors
- `ScriptError` - developer mistakes
- `RequestHumanTakeover` - unrecoverable errors requiring human intervention

### Adding a New Event

1. Create a new directory under `campaign/` (e.g., `event_YYYYMMDD_cn`)
2. Add map YAML files in the new directory
3. Update the event table in `campaign/Readme.md`
4. Run `python -m module.config.config_updater`
5. Add corresponding template images in `assets/cn/event/`

### Adding a New Feature

1. Create a new module directory under `module/`
2. Create a handler class with a `run()` method
3. Add the task method to `AzurLaneAutoScript` in `alas.py`
4. Add config schema to `module/config/argument/argument.yaml` and task mapping to `task.yaml`
5. Run `python -m module.config.config_updater`
6. Add UI template images to `assets/`

## Testing

No formal Python test suite exists. The webapp has a basic Playwright test (`webapp/tests/app.spec.js`). Testing is primarily done by running tasks against a live emulator instance.

## Notes

- This fork has modified `alas.py`'s `run()` method to raise exceptions instead of calling `exit(1)`, allowing the scheduler loop to catch and retry
- Server regions (CN/EN/JP/TW) use different template images in `assets/`
- The `bin/` directory contains screenshot capture tools; the default method varies by platform
- Map files in `campaign/` are YAML definitions of grid layouts, enemy positions, and spawn points
- Operation Siren (OS/大世界) is the most complex feature, spanning `module/os/`, `module/os_combat/`, `module/os_handler/`, `module/os_ash/`, and `module/os_shop/`
