# Cross-Stitch Design Search Utility (Electron Desktop & Web)

A utility to read all the Cross-Stitch Designs I have created and search through them in a variety of ways. It pairs directory scanning with a CSV tracking sheet so I can quickly check design status and model stitcher assignments from my desktop app or phone browser.

## Features

* **Desktop App & Web Access:** Runs as a standalone desktop application via an Electron wrapper (`main.js` / `preload.js`) or through a standard web browser for mobile devices on the local network.
* **Model Stitcher Visibility:** Shows who, if anybody, currently has an unreleased design for model stitching.
* **Design Name Search:** Searches by part or all of a design name, creation date (YYMMDD), or completion status (Finished vs. WIP).
* **Stitcher Assignment Filter:** Filters for designs with or without a model stitcher assigned, or lists all unfinished designs a specific stitcher currently has.
* **Partial Stitcher Search:** Searches by partial stitcher name, returning all matching stitchers alongside the designs they are currently stitching.
* **Priority Sorting:** Sorts designs by oldest first to highlight older unfinished pieces.

## How It Works

* **Design Directories:** Scans two main design directories—including any nested subdirectories of designs—to gather project names, creation dates, and completion status.
* **Stitcher Data:** Reads live model stitcher assignments directly from a local CSV file (`current wips.csv`) with typo-tolerant matching. Stitcher names are Twitch/Discord handles rather than real names.
* **Backend & Interface:** Uses Python and Django for the backend and search logic, paired with custom HTML5 and CSS that adapts fluidly across the Electron desktop window and mobile browsers.

## Running the Electron Desktop App

1. **Navigate to the project root:**
   ```bash
   cd ~/code/myproject
   ```

2. **Install Node/Electron dependencies** (first time only):
   ```bash
   npm install
   ```

3. **Launch the desktop app** (ensure your Python virtual environment is set up at `~/.venv` or active):
   ```bash
   npm start
   ```

## Running Locally for Mobile / Browser Access

1. **Activate the virtual environment from the project root (`~/code/myproject`):**
   ```bash
   source ~/.venv/bin/activate
   ```

2. **Start the Django development server** (allowing access from both this computer and devices on the local Wi-Fi network):
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

3. **Open in a browser:**
   * **On this computer:** Go to `http://127.0.0.1:8000`
   * **On an iPhone or other local device:** Go to `http://<your-computer-ip>:8000/` (find the IP on Linux with `hostname -I`).

4. **Updating stitcher assignments:** Export or overwrite `search_app/current wips.csv` at any time—changes appear on the next search without restarting the app or server.

## Background

I have about 15 years of experience in COBOL, plus HTML5 and CSS for the web pages those systems displayed. This is the same kind of structured file-processing work translated into Python, Django, and JavaScript—the new part is learning the modern web and desktop stack, not learning how to program.
