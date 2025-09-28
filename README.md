# ⚡ Script Runner

A modern **Python + PySide6** utility to run **Python, Bash, and PowerShell** scripts with a graphical interface, real-time output, and automatic log saving.  
Perfect for developers and sysadmins who want a friendlier alternative to the command line.

---

## ✨ Features

- ▶️ **Run scripts**: Python (`.py`), Bash (`.sh`), and PowerShell (`.ps1`)
- 📡 **Real-time output** with syntax highlighting (errors in red, warnings in orange, etc.)
- 📂 **Script history** with quick re-run
- 🗂️ **Sidebar with tabs** for History and Logs
- 💾 **Automatic log saving** in `~/.script_runner/logs/`
- 🎨 **Light/Dark theme toggle**, saved in config (`~/.script_runner/config.json`)
- 🖱️ **Drag & Drop** support and **"Open With"** integration

---

## 📸 Screenshots


<img width="1315" height="789" alt="image" src="https://github.com/user-attachments/assets/7d1fb2de-8a78-4621-b364-6c9b70b9d5de" />

<img width="1315" height="789" alt="image" src="https://github.com/user-attachments/assets/443e73b9-112a-49e7-a692-9ec25968afc4" />

---

## 🔧 Installation

Clone the repository:

```bash
git clone https://github.com/your-username/script-runner.git
cd script-runner


```
Create a virtual environment and install dependencies:

```
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

pip install -r requirements.txt

```

## ▶️ Usage

Run directly:
```
python app.py

```

-   Drag and drop a script into the window, or
    
-   Use the **Browse** button to select one.
    

## 📦 Build for Windows (.exe)

Use **PyInstaller**:

```
pyinstaller --onefile --windowed --icon=app_icon.ico --add-data "app_icon.ico;." app.py

```

The final executable will be in the `dist/` folder.

## 📂 Configuration & Logs

-   Config and history: `~/.script_runner/config.json`
    
-   Saved logs: `~/.script_runner/logs/`
    

## 🛠️ Built With

-   Python 3.11+
    
-   PySide6
    
-   PyInstaller
    

## 🤝 Contributing

Contributions are welcome! Open an **issue** or submit a **pull request** with improvements.

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
