Script Runner
=============

Script Runner is a neon-styled desktop companion for launching automation scripts without leaving a graphical interface. It wraps Python, Bash, PowerShell, and Node.js commands in a modern PySide6 experience: drag a file into the window, tweak arguments with autocomplete, watch live output with inline highlighting, and keep your entire run history searchable.

Highlights
----------

- **Integrated console** - Run scripts in a docked terminal panel with timestamped output, keyword highlighting, and inline command entry.
- **History and logs** - Every run is timestamped, searchable, and one click away from reopening or deleting. Logs live in the sidebar with filters for errors, warnings, and successes.
- **Command templates and autocomplete** - Quick-start snippets for common jobs plus argument autocompletion fed by your recent flags.
- **Interpreter profiles** - Save custom interpreter commands (different Python installs, Node runners, and more) and swap them from the toolbar.
- **Environment aware UI** - Neon dark and crisp light themes, themed scrollbars, centered action buttons, and keyboard shortcuts (Ctrl+R run, Ctrl+Shift+R stop, Ctrl+L clear, Ctrl+O browse).
- **Packaging ready** - One PyInstaller command produces a single-file EXE with bundled icon and assets.

Getting Started
---------------

## 📸 Screenshots


<img width="1372" height="908" alt="image" src="https://github.com/user-attachments/assets/4b7928ce-70dc-474e-81f2-27bc070adb81" />


<img width="1372" height="909" alt="image" src="https://github.com/user-attachments/assets/6a361a8d-c2fb-45d6-9b56-992f07d2d645" />

### Requirements

- Python 3.10 or newer
- pip / virtual environment (recommended)

### Install dependencies

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

At minimum the project depends on PySide6. The virtual environment step keeps the UI runtime isolated from your system Python.

### Launch the app

```
python script_runner.py
```

Drag a `.py`, `.sh`, `.ps1`, or `.js` file onto the window or click **Browse**, adjust arguments, then hit **Run**.

### Keyboard shortcuts

- `Ctrl + R` - Start script
- `Ctrl + Shift + R` - Stop script
- `Ctrl + L` - Clear console
- `Ctrl + O` - Browse for script

Building a Single-File EXE
--------------------------

With the virtual environment activated:

```
pip install pyinstaller
pyinstaller --onefile --windowed --icon app_icon.ico --add-data "app_icon.ico;." script_runner.py
```

The executable is created in `dist/script_runner.exe`. The `--add-data` flag keeps the application icon available at runtime; the main window also applies the icon programmatically, so the packaged app shows your branding in the title bar and taskbar.

Project Structure
-----------------

```
runner_app/
  app.py             # QApplication bootstrap
  config.py          # JSON config loading/saving
  highlighting.py    # QTextEdit syntax highlighter
  paths.py           # resource/config/log path helpers
  process.py         # QProcess wrapper with timestamped output
  settings.py        # Settings dialog and interpreter profiles
  ui/
    main_window.py   # Neon UI layout, console, history, logs
    theme.py         # Theme stylesheet builder (dark/light)
script_runner.py     # Entry point (delegates to runner_app.app)
app_icon.ico         # Application icon
requirements.txt     # Python dependencies
```

Logs and configuration files are stored under `%USERPROFILE%\.script_runner`, keeping the workspace clean.

Development Notes
-----------------

- **Themes** - The stylesheet generator handles both dark and light modes, including custom scrollbars, buttons, and dialogs. Toggle the theme in Settings and it will persist between sessions.
- **Autocomplete** - Argument suggestions are seeded with common CLI flags and populated with flags you use. The completer updates automatically whenever a new argument is typed or sent to the console.
- **Profiles and environments** - Settings -> "Save profile" stores interpreter commands (for example, `C:\Python311\python.exe`) with default arguments. You can clear profiles, history, and logs directly from the dialog.
- **History search** - Use the sidebar search box to filter runs by timestamp or filename. Each entry stores the original arguments so you can rerun recurring jobs in one click.

License
-------

This project is provided under the MIT License. See [LICENSE](LICENSE) if present, or add your preferred license file before publishing.

---

Feel free to open issues or PRs on GitHub if you extend the runner; there is room for more interpreter types, project-specific templates, or integration with task schedulers. Happy scripting!



