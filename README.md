# ASCII Formatter 95

ASCII Formatter 95 is a small offline Windows formatter that turns ordinary notes into a clean, decorative plain-text document.

It includes:

- a Windows 95-inspired interface;
- separate fields for a title, information, explanation, and reason;
- an automatically generated ASCII-art title;
- boxed sections with consistent spacing and line wrapping;
- a live full-document preview;
- one-click copying to the clipboard;
- export to a UTF-8 `.txt` file;
- adjustable output width.

## Download and use

Download `ASCII-Formatter-95.exe`, open it, fill in the fields on the left, and use **Copy** or **Export...**. Windows may show a SmartScreen prompt because the executable is not code-signed.

The formatter runs locally and contains no networking or tracking features.

## Run from source

Python 3 with Tkinter is required:

```powershell
python ascii_formatter.py
```

## Build the executable

```powershell
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed --name ASCII-Formatter-95 ascii_formatter.py
```

The executable will appear in `dist`.

## Privacy and responsible use

Only format information you have permission to use. Avoid publishing private personal, financial, medical, or identifying data.

## License

MIT
