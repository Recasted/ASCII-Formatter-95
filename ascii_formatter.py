import os
import re
import sys
import textwrap
import tkinter as tk
from difflib import get_close_matches
from tkinter import filedialog, messagebox, ttk

try:
    from pyfiglet import Figlet, FigletFont
except ImportError:
    Figlet = FigletFont = None


BG = "#c0c0c0"
BLUE = "#000080"
WHITE = "#ffffff"
BLACK = "#000000"


FONT = {
    "A": ["  A  ", " A A ", "AAAAA", "A   A", "A   A"],
    "B": ["BBBB ", "B   B", "BBBB ", "B   B", "BBBB "],
    "C": [" CCC ", "C   C", "C    ", "C   C", " CCC "],
    "D": ["DDD  ", "D  D ", "D   D", "D  D ", "DDD  "],
    "E": ["EEEEE", "E    ", "EEEE ", "E    ", "EEEEE"],
    "F": ["FFFFF", "F    ", "FFFF ", "F    ", "F    "],
    "G": [" GGG ", "G    ", "G GGG", "G   G", " GGG "],
    "H": ["H   H", "H   H", "HHHHH", "H   H", "H   H"],
    "I": ["IIIII", "  I  ", "  I  ", "  I  ", "IIIII"],
    "J": ["JJJJJ", "   J ", "   J ", "J  J ", " JJ  "],
    "K": ["K   K", "K  K ", "KKK  ", "K  K ", "K   K"],
    "L": ["L    ", "L    ", "L    ", "L    ", "LLLLL"],
    "M": ["M   M", "MM MM", "M M M", "M   M", "M   M"],
    "N": ["N   N", "NN  N", "N N N", "N  NN", "N   N"],
    "O": [" OOO ", "O   O", "O   O", "O   O", " OOO "],
    "P": ["PPPP ", "P   P", "PPPP ", "P    ", "P    "],
    "Q": [" QQQ ", "Q   Q", "Q Q Q", "Q  Q ", " QQ Q"],
    "R": ["RRRR ", "R   R", "RRRR ", "R  R ", "R   R"],
    "S": [" SSSS", "S    ", " SSS ", "    S", "SSSS "],
    "T": ["TTTTT", "  T  ", "  T  ", "  T  ", "  T  "],
    "U": ["U   U", "U   U", "U   U", "U   U", " UUU "],
    "V": ["V   V", "V   V", "V   V", " V V ", "  V  "],
    "W": ["W   W", "W   W", "W W W", "WW WW", "W   W"],
    "X": ["X   X", " X X ", "  X  ", " X X ", "X   X"],
    "Y": ["Y   Y", " Y Y ", "  Y  ", "  Y  ", "  Y  "],
    "Z": ["ZZZZZ", "   Z ", "  Z  ", " Z   ", "ZZZZZ"],
    "0": [" 000 ", "0  00", "0 0 0", "00  0", " 000 "],
    "1": ["  1  ", " 11  ", "  1  ", "  1  ", "11111"],
    "2": [" 222 ", "2   2", "   2 ", "  2  ", "22222"],
    "3": ["3333 ", "    3", " 333 ", "    3", "3333 "],
    "4": ["4  4 ", "4  4 ", "44444", "   4 ", "   4 "],
    "5": ["55555", "5    ", "5555 ", "    5", "5555 "],
    "6": [" 666 ", "6    ", "6666 ", "6   6", " 666 "],
    "7": ["77777", "   7 ", "  7  ", " 7   ", "7    "],
    "8": [" 888 ", "8   8", " 888 ", "8   8", " 888 "],
    "9": [" 999 ", "9   9", " 9999", "    9", " 999 "],
    " ": ["   "] * 5,
    "-": ["     ", "     ", "-----", "     ", "     "],
}


def ascii_title(value, style="graffiti"):
    value = value.strip().upper() or "UNTITLED"
    if Figlet is not None and style != "sog95_block":
        try:
            rendered = Figlet(font=style, width=10000).renderText(value)
            lines = [line.rstrip() for line in rendered.splitlines()]
            while lines and not lines[-1]:
                lines.pop()
            if lines:
                return "\n".join(lines)
        except Exception:
            pass
    supported = "".join(c for c in value if c in FONT)
    if supported != value:
        value = supported or "UNTITLED"
    return "\n".join(" ".join(FONT[c][row] for c in value).rstrip() for row in range(5))


def _tree_items(value):
    """Turn free-form lines into stable, readable tree entries."""
    pairs, plain = [], []
    for raw in value.splitlines():
        line = raw.strip().lstrip("-*• ").strip()
        if not line:
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            if key.strip() and val.strip():
                pairs.append((key.strip(), val.strip()))
                continue
        plain.append(line)
    pairs.sort(key=lambda item: item[0].casefold())
    return [(key, val) for key, val in pairs] + [("", line) for line in plain]


def _classify_information(value):
    """Classify input lines by their content without sending data anywhere."""
    buckets = {}
    patterns = (
        ("PASSWORDS / CREDENTIALS", re.compile(r"\b(pass(?:word|code)?|pwd|credential|login|token|secret|pin)\b", re.I)),
        ("EMAIL ADDRESSES", re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")),
        ("IP ADDRESSES", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b|\b[0-9a-f]{0,4}:[0-9a-f:]+\b", re.I)),
        ("WEB LINKS / DOMAINS", re.compile(r"\b(?:https?://|www\.|[\w-]+\.(?:com|net|org|io|dev|gg|co|nl)\b)", re.I)),
        ("PHONE NUMBERS", re.compile(r"(?:\+?\d[\d ()-]{7,}\d)")),
        ("FINANCIAL INFORMATION", re.compile(r"\b(bank|iban|swift|routing|card|credit|debit|payment|mortgage|balance|\$|€|£)\b", re.I)),
        ("LOCATIONS / ADDRESSES", re.compile(r"\b(address|street|road|avenue|city|state|country|postal|postcode|zip|location|coordinates?)\b", re.I)),
        ("ACCOUNTS / USERNAMES", re.compile(r"\b(account|username|user name|alias|handle|profile|discord|telegram|instagram|twitter|github)\b", re.I)),
        ("DATES / TIMELINE", re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|date|born|birthday|created|updated)\b", re.I)),
        ("IDENTITY / PERSONAL", re.compile(r"\b(name|age|gender|pronouns?|occupation|school|employer|family|mother|father|sister|brother)\b", re.I)),
        ("DEVICES / SYSTEM", re.compile(r"\b(device|computer|windows|linux|mac|android|iphone|hostname|browser|operating system|hardware)\b", re.I)),
    )
    for raw in value.splitlines():
        line = raw.strip()
        if not line:
            continue
        category = "OTHER INFORMATION"
        for label, pattern in patterns:
            if pattern.search(line):
                category = label
                break
        buckets.setdefault(category, []).append(line)
    if not buckets:
        buckets["OTHER INFORMATION"] = ["(none provided)"]
    order = [label for label, _ in patterns] + ["OTHER INFORMATION"]
    return [(label, "\n".join(buckets[label])) for label in order if label in buckets]


def make_document(title, info, explanation, reason, minimum_width=82, auto_fit=True,
                  title_style="graffiti"):
    art_lines = ascii_title(title, title_style).splitlines()
    sections = _classify_information(info)
    brief_items = []
    if explanation.strip():
        brief_items.append(("Explanation", explanation.strip()))
    if reason.strip():
        brief_items.append(("Reason", reason.strip()))
    if not brief_items:
        brief_items.append(("Brief", "(none provided)"))

    raw_lines = [line.strip() for _, value in sections + brief_items for line in value.splitlines() if line.strip()]
    longest_input = max([len(line) + 12 for line in raw_lines] or [0])
    required = max([len(line) for line in art_lines] + [len(title) + 12, longest_input, 82])
    inner = max(64, int(minimum_width), required if auto_fit else 0)

    def content(value="", align="left"):
        value = value[:inner]
        padded = value.center(inner) if align == "center" else value.ljust(inner)
        return f"-(║)- {padded} -(║)-"

    def divider(char="═"):
        filler = inner + 5
        left = (filler + 1) // 2
        right = filler - left
        return f"-(╠{char * left}&{char * right}╣)-"

    def tree(value):
        items = _tree_items(value)
        output = []
        for index, (key, val) in enumerate(items):
            last = index == len(items) - 1
            branch = "└──" if last else "├──"
            continuation = "   " if last else "│  "
            if key:
                output.append(content(f"{branch} {key}"))
                wrapped = textwrap.wrap(val, max(20, inner - 7), replace_whitespace=False) or [""]
                for part_index, part in enumerate(wrapped):
                    twig = "└─" if part_index == len(wrapped) - 1 else "├─"
                    output.append(content(f"{continuation} {twig} {part}"))
            else:
                wrapped = textwrap.wrap(val, max(20, inner - 5), replace_whitespace=False) or [""]
                for part_index, part in enumerate(wrapped):
                    mark = branch if part_index == 0 else continuation + "  "
                    output.append(content(f"{mark} {part}"))
        return output

    lines = [divider()]
    art_width = max(len(line) for line in art_lines)
    for line in art_lines:
        # Center the complete FIGlet canvas, not each row independently.
        # Individual row centering makes shorter lower strokes drift right.
        lines.append(content(line.ljust(art_width), "center"))
    lines += [content(), divider(), content("BRIEF // EXPLANATION & REASON", "center"), content()]
    for index, (label, value) in enumerate(brief_items):
        last = index == len(brief_items) - 1
        branch = "└──" if last else "├──"
        continuation = "   " if last else "│  "
        lines.append(content(f"{branch} {label}"))
        wrapped = textwrap.wrap(value, max(20, inner - 7), replace_whitespace=False) or [""]
        for part_index, part in enumerate(wrapped):
            twig = "└─" if part_index == len(wrapped) - 1 else "├─"
            lines.append(content(f"{continuation} {twig} {part}"))
    lines += [content(), divider(), content("AUTOMATIC INFORMATION INDEX", "center"), content()]
    for index, (label, _) in enumerate(sections, 1):
        connector = "└──" if index == len(sections) else "├──"
        lines.append(content(f"{connector} {index:02d}. {label.title()}"))
    lines += [content(), divider()]

    for index, (label, value) in enumerate(sections, 1):
        lines += [content(f"[ {index:02d} // {label} ]", "center"), content()]
        lines += tree(value)
        lines += [content(), divider()]
    lines += [content("Generated by Sog95", "center"),
              content("Created by https://doxbin.com/user/k1ck / https://t.me/cartelleader", "center"),
              divider()]
    return "\n".join(lines)


class RaisedButton(tk.Button):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, fg=BLACK, activebackground=BG,
                         relief="raised", bd=3, font=("MS Sans Serif", 9, "bold"),
                         padx=12, pady=3, **kwargs)


class App:
    def __init__(self, root):
        self.root = root
        self.auto_fit = tk.BooleanVar(value=True)
        root.title("Sog95")
        icon_path = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(__file__)), "ascii_formatter_95.ico")
        if os.path.exists(icon_path):
            try:
                root.iconbitmap(icon_path)
            except tk.TclError:
                pass
        root.geometry("1120x720")
        root.minsize(850, 560)
        root.configure(bg=BG)

        titlebar = tk.Frame(root, bg=BLUE, bd=2, relief="raised")
        titlebar.pack(fill="x", padx=4, pady=(4, 0))
        tk.Label(titlebar, text="▣  Sog95 — ASCII Formatter", bg=BLUE, fg=WHITE,
                 font=("MS Sans Serif", 10, "bold"), anchor="w").pack(side="left", fill="x", expand=True, padx=5, pady=3)
        tk.Button(titlebar, text="?", width=3, bg=BG, relief="raised", bd=2,
                  command=self.about).pack(side="right", padx=2, pady=2)

        toolbar = tk.Frame(root, bg=BG, bd=2, relief="raised")
        toolbar.pack(fill="x", padx=4)
        self.add_menu(toolbar, "File", (("Export...", self.export), (None, None), ("Exit", root.destroy)))
        self.add_menu(toolbar, "Edit", (("Copy all", self.copy), ("Clear fields", self.clear)))
        self.add_menu(toolbar, "Format", (("Auto-fit width", self.toggle_auto_fit, "check"),))
        self.add_menu(toolbar, "Help", (("About Sog95", self.about),))

        main = tk.PanedWindow(root, orient="horizontal", bg=BG, sashwidth=7, bd=2, relief="sunken")
        main.pack(fill="both", expand=True, padx=7, pady=7)
        left = tk.Frame(main, bg=BG, width=310, bd=2, relief="raised")
        right = tk.Frame(main, bg=BG, bd=2, relief="sunken")
        main.add(left, minsize=270)
        main.add(right, minsize=500)

        tk.Label(left, text="Document fields", bg=BLUE, fg=WHITE,
                 font=("MS Sans Serif", 9, "bold"), anchor="w").pack(fill="x", padx=4, pady=4)
        self.title = self.field(left, "Title", one_line=True)
        style_frame = tk.Frame(left, bg=BG)
        style_frame.pack(fill="x", padx=8, pady=(0, 4))
        tk.Label(style_frame, text="ASCII title style:", bg=BG, anchor="w",
                 font=("MS Sans Serif", 8, "bold")).pack(fill="x")
        fonts = sorted(FigletFont.getFonts(), key=str.casefold) if FigletFont else []
        self.title_styles = ["sog95_block"] + fonts
        style_controls = tk.Frame(style_frame, bg=BG)
        style_controls.pack(fill="x")
        self.style_search = tk.Entry(style_controls, width=11, relief="sunken", bd=2,
                                     font=("MS Sans Serif", 8))
        self.style_search.pack(side="left", fill="x", expand=True)
        self.style_search.insert(0, "Search styles...")
        self.style_search.configure(fg="#606060")
        self.style_search.bind("<FocusIn>", self.clear_style_placeholder)
        self.style_search.bind("<FocusOut>", self.restore_style_placeholder)
        self.style_search.bind("<KeyRelease>", self.filter_title_styles)
        self.style_search.bind("<Return>", self.choose_first_style)
        self.title_style = ttk.Combobox(style_controls, values=self.title_styles,
                                        state="readonly", height=18, width=19)
        self.title_style.set("graffiti" if "graffiti" in self.title_styles else "sog95_block")
        self.title_style.pack(side="right", fill="x", expand=True, padx=(7, 0))
        self.title_style.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        self.info = self.field(left, "Information")
        self.explanation = self.field(left, "Explanation")
        self.reason = self.field(left, "Reason")

        options = tk.LabelFrame(left, text="Options", bg=BG, font=("MS Sans Serif", 9))
        options.pack(fill="x", padx=8, pady=6)
        tk.Label(options, text="Minimum width:", bg=BG).pack(side="left", padx=5, pady=6)
        self.width = tk.Spinbox(options, from_=64, to=9999, width=5, relief="sunken", bd=2, command=self.refresh)
        self.width.delete(0, "end"); self.width.insert(0, "82")
        self.width.pack(side="left")
        tk.Checkbutton(options, text="Auto-fit", variable=self.auto_fit, bg=BG,
                       activebackground=BG, command=self.refresh).pack(side="left", padx=7)

        buttons = tk.Frame(left, bg=BG)
        buttons.pack(fill="x", padx=7, pady=7)
        RaisedButton(buttons, text="Copy", command=self.copy).pack(side="left", padx=2)
        RaisedButton(buttons, text="Export...", command=self.export).pack(side="left", padx=2)

        tk.Label(right, text="Full generated file preview", bg=BLUE, fg=WHITE,
                 font=("MS Sans Serif", 9, "bold"), anchor="w").pack(fill="x", padx=4, pady=4)
        preview_frame = tk.Frame(right, bg=BG, bd=2, relief="sunken")
        preview_frame.pack(fill="both", expand=True, padx=7, pady=(0, 7))
        self.preview = tk.Text(preview_frame, wrap="none", bg=WHITE, fg=BLACK,
                               font=("Consolas", 9), undo=False, relief="flat")
        y = tk.Scrollbar(preview_frame, command=self.preview.yview)
        x = tk.Scrollbar(preview_frame, orient="horizontal", command=self.preview.xview)
        self.preview.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        self.preview.grid(row=0, column=0, sticky="nsew")
        y.grid(row=0, column=1, sticky="ns"); x.grid(row=1, column=0, sticky="ew")
        preview_frame.grid_rowconfigure(0, weight=1); preview_frame.grid_columnconfigure(0, weight=1)
        self.preview.bind("<ButtonPress-2>", self.start_pan)
        self.preview.bind("<B2-Motion>", self.drag_pan)
        self.preview.bind("<ButtonRelease-2>", self.end_pan)
        self.preview.bind("<Shift-MouseWheel>", self.horizontal_wheel)

        self.status = tk.Label(root, text="Ready", bg=BG, bd=2, relief="sunken", anchor="w")
        self.status.pack(fill="x", padx=5, pady=(0, 5))
        self.title.insert(0, "MY REPORT")
        for widget in (self.title, self.info, self.explanation, self.reason):
            widget.bind("<KeyRelease>", lambda _e: self.refresh())
        self.refresh()

    def add_menu(self, parent, label, commands):
        button = tk.Menubutton(parent, text=label, bg=BG, activebackground=BLUE,
                               activeforeground=WHITE, relief="flat", padx=8, pady=3)
        menu = tk.Menu(button, tearoff=False, bg=BG, activebackground=BLUE,
                       activeforeground=WHITE, relief="raised", bd=2)
        for item in commands:
            if item[0] is None:
                menu.add_separator()
            elif len(item) > 2 and item[2] == "check":
                menu.add_checkbutton(label=item[0], variable=self.auto_fit,
                                     command=self.refresh)
            else:
                menu.add_command(label=item[0], command=item[1])
        button.configure(menu=menu)
        button.pack(side="left")

    def start_pan(self, event):
        self.preview.configure(cursor="fleur")
        self.preview.scan_mark(event.x, event.y)
        return "break"

    def clear_style_placeholder(self, _event):
        if self.style_search.get() == "Search styles...":
            self.style_search.delete(0, "end")
            self.style_search.configure(fg=BLACK)

    def restore_style_placeholder(self, _event):
        if not self.style_search.get().strip():
            self.style_search.insert(0, "Search styles...")
            self.style_search.configure(fg="#606060")
            self.title_style.configure(values=self.title_styles)

    def matching_styles(self):
        query = self.style_search.get().strip().casefold()
        if not query or query == "search styles...":
            return self.title_styles
        direct = [style for style in self.title_styles if query in style.casefold()]
        if direct:
            return sorted(direct, key=lambda style: (
                style.casefold() != query,
                not style.casefold().startswith(query),
                style.casefold(),
            ))
        # Tolerate small spelling differences, e.g. "calligrafy" -> "caligraphy".
        return get_close_matches(query, self.title_styles, n=30, cutoff=0.35)

    def filter_title_styles(self, _event=None):
        matches = self.matching_styles()
        self.title_style.configure(values=matches)
        query = self.style_search.get().strip().casefold()
        exact = next((style for style in matches if style.casefold() == query), None)
        if exact:
            self.title_style.set(exact)
            self.refresh()

    def choose_first_style(self, _event=None):
        matches = self.matching_styles()
        if matches:
            self.title_style.set(matches[0])
            self.refresh()
            self.status.configure(text=f"ASCII title style: {matches[0]}")
        return "break"

    def drag_pan(self, event):
        self.preview.scan_dragto(event.x, event.y, gain=1)
        return "break"

    def end_pan(self, _event):
        self.preview.configure(cursor="xterm")
        return "break"

    def horizontal_wheel(self, event):
        direction = -1 if event.delta > 0 else 1
        self.preview.xview_scroll(direction * 4, "units")
        return "break"

    def toggle_auto_fit(self):
        self.auto_fit.set(not self.auto_fit.get())
        self.refresh()

    def clear(self):
        self.title.delete(0, "end")
        for widget in (self.info, self.explanation, self.reason):
            widget.delete("1.0", "end")
        self.refresh()
        self.status.configure(text="All fields cleared")

    def about(self):
        messagebox.showinfo("About Sog95",
                            "Sog95 — ASCII Formatter\n\nA local, offline formatter with automatic sections, ASCII trees, live preview, copying, and text export.")

    def field(self, parent, label, one_line=False):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="x", padx=8, pady=4)
        tk.Label(frame, text=label + ":", bg=BG, anchor="w", font=("MS Sans Serif", 9, "bold")).pack(fill="x")
        if one_line:
            widget = tk.Entry(frame, relief="sunken", bd=2, font=("MS Sans Serif", 9))
            widget.pack(fill="x")
        else:
            widget = tk.Text(frame, height=4, wrap="word", relief="sunken", bd=2, font=("MS Sans Serif", 9))
            widget.pack(fill="x")
        return widget

    @staticmethod
    def value(widget):
        return widget.get() if isinstance(widget, tk.Entry) else widget.get("1.0", "end-1c")

    def result(self):
        try: width = max(64, int(self.width.get()))
        except ValueError: width = 82
        return make_document(self.value(self.title), self.value(self.info),
                             self.value(self.explanation), self.value(self.reason),
                             width, self.auto_fit.get(), self.title_style.get())

    def refresh(self):
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", self.result())
        self.preview.configure(state="disabled")
        self.status.configure(text="Preview updated")

    def copy(self):
        self.root.clipboard_clear(); self.root.clipboard_append(self.result())
        self.root.update()
        self.status.configure(text="Copied the complete formatted text to the clipboard")

    def export(self):
        safe = "".join(c for c in self.value(self.title) if c.isalnum() or c in "-_ ").strip() or "formatted"
        path = filedialog.asksaveasfilename(title="Export formatted text", defaultextension=".txt",
                                            initialfile=safe + ".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path: return
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as handle: handle.write(self.result())
            self.status.configure(text=f"Exported: {os.path.basename(path)}")
            messagebox.showinfo("Export complete", "Your formatted text file was saved.")
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
