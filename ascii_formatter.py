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
    items = []
    current_key = None
    current_values = []

    def flush_group():
        nonlocal current_key, current_values
        if current_key is not None:
            items.append((current_key, "\n".join(current_values), False))
        current_key = None
        current_values = []

    for raw in value.splitlines():
        line = raw.strip().lstrip("-*• ").strip()
        if not line:
            if current_key is not None:
                current_values.append("")
            elif not items or items[-1] != ("", "", False):
                items.append(("", "", False))
            continue
        if line.endswith(":") and line[:-1].strip():
            flush_group()
            current_key = line[:-1].strip()
            continue
        if ":" in line and not re.match(r"^[a-z][a-z0-9+.-]*://", line, re.I):
            key, val = line.split(":", 1)
            if key.strip() and val.strip():
                if current_key is not None:
                    current_values.append("> " + line)
                    continue
                flush_group()
                items.append((key.strip(), val.strip(), True))
                continue
        if current_key is not None:
            current_values.append(line)
        else:
            items.append(("", line, False))
    flush_group()
    return items


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
        ("SOCIAL MEDIA", re.compile(r"\b(social media|snapchat|tiktok|facebook|youtube|reddit|post(?:ed|ing)?|follower)\b", re.I)),
        ("EDUCATION", re.compile(r"\b(education|school|college|university|degree|student|graduate|graduated|course|academic)\b", re.I)),
        ("EMPLOYMENT / OCCUPATION", re.compile(r"\b(employment|employer|employee|occupation|job|work(?:ed|ing)?|company|manager|engineer|intern)\b", re.I)),
        ("RELATIONSHIPS / ASSOCIATES", re.compile(r"\b(relationship|associate|friend|girlfriend|boyfriend|partner|spouse|wife|husband|relative)\b", re.I)),
        ("VEHICLES", re.compile(r"\b(vehicle|car|truck|motorcycle|license plate|registration|vin)\b", re.I)),
        ("DATES / TIMELINE", re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|date|born|birthday|created|updated)\b", re.I)),
        ("IDENTITY / PERSONAL", re.compile(r"\b(name|age|gender|pronouns?|occupation|school|employer|family|mother|father|sister|brother)\b", re.I)),
        ("DEVICES / SYSTEM", re.compile(r"\b(device|computer|windows|linux|mac|android|iphone|hostname|browser|operating system|hardware)\b", re.I)),
        ("LEGAL / COURT INFORMATION", re.compile(r"\b(court|legal|charge|plea|sentence|sentencing|trial|bail|judge|prosecutor|defendant|convicted|custody|probation|hearing|evidence)\b", re.I)),
        ("EVIDENCE / SOURCES", re.compile(r"\b(evidence|source|report|record|document|screenshot|photo|video|archive|statement|admission)\b", re.I)),
        ("INCIDENT / ALLEGATIONS", re.compile(r"\b(incident|allegation|accused|abuse|torture|harm(?:ed|ing)?|kill(?:ed|ing)?|murder|victim|threat|attack|crime)\b", re.I)),
    )
    for raw in value.splitlines():
        line = raw.strip()
        if not line:
            continue
        category = "CONTEXT / SUMMARY"
        for label, pattern in patterns:
            if pattern.search(line):
                category = label
                break
        buckets.setdefault(category, []).append(line)
    if not buckets:
        buckets[""] = ["(none provided)"]
    order = [label for label, _ in patterns] + ["CONTEXT / SUMMARY", ""]
    return [(label, "\n".join(buckets[label])) for label in order if label in buckets]


def make_document(title, info, explanation, reason, minimum_width=82, auto_fit=True,
                  title_style="graffiti", additional_sections=None, info_title=""):
    art_lines = ascii_title(title, title_style).splitlines()
    custom_sections = [
        ((label.strip() or "UNTITLED DIVIDER").upper(), body.strip())
        for label, body in (additional_sections or [])
        if label.strip() or body.strip()
    ]
    if info_title.strip():
        information_sections = [(info_title.strip().upper(), info.strip() or "(none provided)")]
    else:
        information_sections = [(label or "INFORMATION", body)
                                for label, body in _classify_information(info)]
    sections = information_sections + custom_sections
    brief_items = [
        ("EXPLANATION", explanation.strip() or "(none provided)"),
        ("REASON", reason.strip() or "(none provided)"),
    ]

    # The title canvas dictates auto-fit width. Body text always wraps inside it.
    required = max([len(line) for line in art_lines] + [len(title) + 12, 82])
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

    def wrapped_lines(value, width):
        """Wrap every source line separately so embedded newlines cannot break borders."""
        output = []
        for source_line in value.splitlines() or [""]:
            output.extend(textwrap.wrap(source_line, width, replace_whitespace=True,
                                        drop_whitespace=True) or [""])
        return output

    def tree(value, auto_sort=False):
        items = _tree_items(value)
        meaningful = value.strip() and value.strip() != "(none provided)"
        if auto_sort and meaningful and not any(key for key, _val, _inline in items):
            items = [(label.title(), body, False) if label else ("", body, False)
                     for label, body in _classify_information(value)]
        output = []
        for index, (key, val, inline) in enumerate(items):
            last = index == len(items) - 1
            if key:
                if inline:
                    label = f"  » {key}:"
                    prefix = label + " "
                    wrapped = wrapped_lines(val, max(20, inner - len(prefix)))
                    for part_index, part in enumerate(wrapped):
                        output.append(content((prefix if part_index == 0 else " " * len(prefix)) + part))
                else:
                    output.append(content(f"  » {key}:"))
                    children = val.split("\n") if val else ["(none provided)"]
                    for child in children:
                        child = child.strip()
                        if not child:
                            output.append(content())
                            continue
                        subdetail = child.startswith((">", "›"))
                        child = child.lstrip(">› ").strip()
                        prefix = "      › " if subdetail else "        "
                        wrapped = wrapped_lines(child, max(20, inner - len(prefix)))
                        for part_index, part in enumerate(wrapped):
                            output.append(content((prefix if part_index == 0 else " " * len(prefix)) + part))
            else:
                if not val:
                    output.append(content())
                    continue
                subdetail = val.startswith((">", "›"))
                val = val.lstrip(">› ").strip()
                prefix = "      › " if subdetail else "        "
                wrapped = wrapped_lines(val, max(20, inner - len(prefix)))
                for part_index, part in enumerate(wrapped):
                    output.append(content((prefix if part_index == 0 else " " * len(prefix)) + part))
            if not last:
                separator = content()
                if not output or output[-1] != separator:
                    output.append(separator)
        return output

    lines = [divider()]
    art_width = max(len(line) for line in art_lines)
    for line in art_lines:
        # Center the complete FIGlet canvas, not each row independently.
        # Individual row centering makes shorter lower strokes drift right.
        lines.append(content(line.ljust(art_width), "center"))
    lines += [content(), divider()]
    for label, value in brief_items:
        lines += [content(f"[ {label} ]", "center"), content()]
        lines += tree(value, auto_sort=True)
        lines += [content(), divider()]
    for index, (label, value) in enumerate(sections, 1):
        lines += [content(f"[ {index:02d} // {label} ]", "center"), content()]
        lines += tree(value, auto_sort=True)
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
        self.warned_char_thresholds = set()
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
        root.after(0, lambda: root.state("zoomed"))

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

        left_scroll = tk.Scrollbar(left, orient="vertical")
        left_scroll.pack(side="right", fill="y")
        self.form_canvas = tk.Canvas(left, bg=BG, highlightthickness=0,
                                     yscrollcommand=left_scroll.set)
        self.form_canvas.pack(side="left", fill="both", expand=True)
        left_scroll.configure(command=self.form_canvas.yview)
        form = tk.Frame(self.form_canvas, bg=BG)
        self.form_container = form
        self.form_window = self.form_canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind("<Configure>", lambda _e: self.form_canvas.configure(
            scrollregion=(0, 0, self.form_canvas.winfo_width(),
                          max(self.form_canvas.winfo_height(), form.winfo_reqheight()))))
        self.form_canvas.bind("<Configure>", lambda e: (
            self.form_canvas.itemconfigure(self.form_window, width=e.width),
            self.form_canvas.configure(scrollregion=(0, 0, e.width,
                max(e.height, form.winfo_reqheight())))))
        self.form_canvas.bind("<MouseWheel>", self.scroll_form)
        self.root.bind_all("<MouseWheel>", self.route_mousewheel, add="+")
        # Always open at the first field; extra space and scrolling belong below it.
        self.root.after(100, lambda: self.form_canvas.yview_moveto(0))

        tk.Label(form, text="Document fields", bg=BLUE, fg=WHITE,
                 font=("MS Sans Serif", 9, "bold"), anchor="w").pack(fill="x", padx=4, pady=4)
        self.title = self.field(form, "Title", one_line=True)
        style_frame = tk.Frame(form, bg=BG)
        style_frame.pack(fill="x", padx=8, pady=(0, 4))
        tk.Label(style_frame, text="ASCII title style:", bg=BG, anchor="w",
                 font=("MS Sans Serif", 8, "bold")).pack(fill="x")
        fonts = sorted(FigletFont.getFonts(), key=str.casefold) if FigletFont else []
        self.title_styles = ["sog95_block"] + fonts
        style_controls = tk.Frame(style_frame, bg=BG)
        style_controls.pack(fill="x")
        self.title_style = ttk.Combobox(style_controls, values=self.title_styles,
                                        state="normal", height=18)
        self.title_style.set("graffiti" if "graffiti" in self.title_styles else "sog95_block")
        self.title_style.pack(fill="x")
        self.title_style.bind("<KeyRelease>", self.filter_title_styles)
        self.title_style.bind("<Return>", self.choose_first_style)
        self.title_style.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        self.title_style.bind("<Button-1>", self.prepare_style_popup, add="+")
        self._style_popup_typed = False
        self._style_popup_command = self.root.register(self.type_in_style_popup)
        self.explanation = self.field(form, "Explanation")
        self.reason = self.field(form, "Reason")
        self.info_title = self.field(form, "Main information section title", one_line=True)
        self.info_title.insert(0, "Information")
        self.info = self.field(form, "Information")

        self.custom_sections = []
        self.extra_area = tk.LabelFrame(form, text="Subtitle / divider boxes (0 / 8)",
                                        bg=BG, font=("MS Sans Serif", 9))
        self.extra_area.pack(fill="x", padx=8, pady=(6, 2))
        self.extra_list = tk.Frame(self.extra_area, bg=BG)
        self.extra_list.pack(fill="x", padx=4, pady=(3, 0))
        RaisedButton(self.extra_area, text="+ Add subtitle / divider",
                     command=self.add_custom_section).pack(fill="x", padx=4, pady=5)

        options = tk.LabelFrame(form, text="Options", bg=BG, font=("MS Sans Serif", 9))
        options.pack(fill="x", padx=8, pady=6)
        tk.Label(options, text="Minimum width:", bg=BG).pack(side="left", padx=5, pady=6)
        self.width = tk.Spinbox(options, from_=64, to=9999, width=5, relief="sunken", bd=2, command=self.refresh)
        self.width.delete(0, "end"); self.width.insert(0, "82")
        self.width.pack(side="left")
        tk.Checkbutton(options, text="Auto-fit", variable=self.auto_fit, bg=BG,
                       activebackground=BG, command=self.refresh).pack(side="left", padx=7)

        buttons = tk.Frame(form, bg=BG)
        buttons.pack(fill="x", padx=7, pady=7)
        RaisedButton(buttons, text="Copy", command=self.copy).pack(side="left", padx=2)
        RaisedButton(buttons, text="Export...", command=self.export).pack(side="left", padx=2)

        preview_header = tk.Frame(right, bg=BLUE, bd=1, relief="raised")
        preview_header.pack(fill="x", padx=4, pady=4)
        tk.Label(preview_header, text="Full generated file preview", bg=BLUE, fg=WHITE,
                 font=("MS Sans Serif", 9, "bold"), anchor="w").pack(
                     side="left", fill="x", expand=True, padx=4)
        self.preview_font_size = 9
        self.preview_zoom_label = tk.Label(preview_header, text="100%", width=5,
                                           bg=BLUE, fg=WHITE,
                                           font=("MS Sans Serif", 8, "bold"))
        self.preview_zoom_label.pack(side="right", padx=(2, 3))
        tk.Button(preview_header, text="+", width=2, bg=BG, relief="raised", bd=2,
                  font=("MS Sans Serif", 8, "bold"), command=lambda: self.zoom_preview(1)).pack(
                      side="right", padx=1, pady=1)
        tk.Button(preview_header, text="−", width=2, bg=BG, relief="raised", bd=2,
                  font=("MS Sans Serif", 8, "bold"), command=lambda: self.zoom_preview(-1)).pack(
                      side="right", padx=1, pady=1)
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
        self.preview.bind("<Control-MouseWheel>", self.control_zoom_preview)

        status_bar = tk.Frame(root, bg=BG)
        status_bar.pack(fill="x", padx=5, pady=(0, 5))
        self.status = tk.Label(status_bar, text="Ready", bg=BG, bd=2,
                               relief="sunken", anchor="w")
        self.status.pack(side="left", fill="x", expand=True)
        self.char_count_label = tk.Label(status_bar, text="Characters: 0", bg=BG,
                                          bd=2, relief="sunken", anchor="e",
                                          width=22, font=("MS Sans Serif", 8, "bold"))
        self.char_count_label.pack(side="right", padx=(4, 0))
        self.title.insert(0, "MY REPORT")
        for widget in (self.title, self.info_title, self.info, self.explanation, self.reason):
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

    def scroll_form(self, event):
        self.form_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"

    def zoom_preview(self, direction):
        self.preview_font_size = max(6, min(28, self.preview_font_size + direction))
        self.preview.configure(font=("Consolas", self.preview_font_size))
        percent = round(self.preview_font_size / 9 * 100)
        self.preview_zoom_label.configure(text=f"{percent}%")
        self.status.configure(text=f"Preview zoom: {percent}%")

    def control_zoom_preview(self, event):
        self.zoom_preview(1 if event.delta > 0 else -1)
        return "break"

    def route_mousewheel(self, event):
        """Scroll the form even when the pointer is over an Entry/Text child."""
        widget = self.root.winfo_containing(self.root.winfo_pointerx(),
                                            self.root.winfo_pointery())
        current = widget
        while current is not None:
            if current is self.form_container or current is self.form_canvas:
                self.form_canvas.yview_scroll(-3 if event.delta > 0 else 3, "units")
                return "break"
            current = getattr(current, "master", None)
        return None

    def add_custom_section(self):
        if len(self.custom_sections) >= 8:
            self.status.configure(text="Maximum of 8 subtitle / divider boxes reached")
            return
        number = len(self.custom_sections) + 1
        card = tk.Frame(self.extra_list, bg="#d4d4d4", bd=2, relief="groove")
        card.pack(fill="x", pady=3)
        header = tk.Frame(card, bg=BLUE)
        header.pack(fill="x")
        tk.Label(header, text=f" Divider {number} ", bg=BLUE, fg=WHITE,
                 font=("MS Sans Serif", 8, "bold")).pack(side="left")
        remove = tk.Button(header, text="×", width=2, bg=BG, bd=1,
                           command=lambda: self.remove_custom_section(card))
        remove.pack(side="right")
        tk.Label(card, text="Section title:", bg="#d4d4d4", anchor="w").pack(fill="x", padx=5, pady=(4, 0))
        title = tk.Entry(card, relief="sunken", bd=2, font=("MS Sans Serif", 8))
        title.insert(0, f"Additional section {number}")
        title.pack(fill="x", padx=5)
        tk.Label(card, text="Content (optional for divider-only):", bg="#d4d4d4", anchor="w").pack(fill="x", padx=5, pady=(4, 0))
        body = tk.Text(card, height=3, wrap="word", relief="sunken", bd=2,
                       font=("MS Sans Serif", 8))
        body.pack(fill="x", padx=5, pady=(0, 5))
        title.bind("<KeyRelease>", lambda _e: self.refresh())
        body.bind("<KeyRelease>", lambda _e: self.refresh())
        self.custom_sections.append({"frame": card, "title": title, "body": body})
        self.update_extra_label()
        self.refresh()
        self.root.after_idle(lambda: self.form_canvas.yview_moveto(1.0))

    def remove_custom_section(self, card):
        match = next((item for item in self.custom_sections if item["frame"] is card), None)
        if match:
            self.custom_sections.remove(match)
            card.destroy()
            self.update_extra_label()
            self.refresh()

    def update_extra_label(self):
        self.extra_area.configure(text=f"Subtitle / divider boxes ({len(self.custom_sections)} / 8)")

    def custom_section_values(self):
        return [(self.value(item["title"]), self.value(item["body"]))
                for item in self.custom_sections]

    def start_pan(self, event):
        self.preview.configure(cursor="fleur")
        self.preview.scan_mark(event.x, event.y)
        return "break"

    def matching_styles(self):
        query = self.title_style.get().strip().casefold()
        if not query:
            return self.title_styles
        search_query = query.replace("calli", "cali")
        direct = [style for style in self.title_styles if search_query in style.casefold()]
        if direct:
            return sorted(direct, key=lambda style: (
                style.casefold() != search_query,
                not style.casefold().startswith(search_query),
                style.casefold(),
            ))
        # Tolerate small spelling differences, e.g. "calligrafy" -> "caligraphy".
        return get_close_matches(search_query, self.title_styles, n=30, cutoff=0.35)

    def prepare_style_popup(self, _event=None):
        """Let keystrokes edit/filter the combobox even while its list is open."""
        self._style_popup_typed = False
        self.root.after(20, self.bind_style_popup)

    def bind_style_popup(self):
        try:
            popup = self.root.tk.call("ttk::combobox::PopdownWindow", str(self.title_style))
            listbox = f"{popup}.f.l"
            script = f'if {{[{self._style_popup_command} %A %K] eq "break"}} {{break}}'
            self.root.tk.call("bind", listbox, "<KeyPress>", script)
        except tk.TclError:
            pass

    def type_in_style_popup(self, character, keysym):
        if keysym == "BackSpace":
            query = self.title_style.get() if self._style_popup_typed else ""
            self.title_style.set(query[:-1])
        elif character and character.isprintable():
            query = self.title_style.get() if self._style_popup_typed else ""
            self.title_style.set(query + character)
        else:
            return ""
        self._style_popup_typed = True
        matches = self.matching_styles()
        self.title_style.configure(values=matches)
        try:
            popup = self.root.tk.call("ttk::combobox::PopdownWindow", str(self.title_style))
            listbox = f"{popup}.f.l"
            self.root.tk.call(listbox, "delete", 0, "end")
            for style in matches:
                self.root.tk.call(listbox, "insert", "end", style)
            if matches:
                self.root.tk.call(listbox, "selection", "set", 0)
                self.root.tk.call(listbox, "see", 0)
        except tk.TclError:
            pass
        return "break"

    def filter_title_styles(self, _event=None):
        matches = self.matching_styles()
        self.title_style.configure(values=matches)
        query = self.title_style.get().strip().casefold()
        exact = next((style for style in matches if style.casefold() == query), None)
        if exact:
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
        self.info_title.delete(0, "end")
        self.info_title.insert(0, "Information")
        for widget in (self.info, self.explanation, self.reason):
            widget.delete("1.0", "end")
        for item in list(self.custom_sections):
            item["frame"].destroy()
        self.custom_sections.clear()
        self.update_extra_label()
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
                             width, self.auto_fit.get(), self.title_style.get(),
                             self.custom_section_values(), self.value(self.info_title))

    def input_character_count(self):
        total = sum(len(self.value(widget)) for widget in
                    (self.title, self.info_title, self.explanation, self.reason, self.info))
        for item in self.custom_sections:
            total += len(self.value(item["title"])) + len(self.value(item["body"]))
        return total

    def check_character_warnings(self):
        count = self.input_character_count()
        colour = "#800000" if count > 1_000_000 else ("#805000" if count > 100_000 else BLACK)
        self.char_count_label.configure(text=f"Characters: {count:,}", fg=colour)
        thresholds = (
            (100_000, "Large document warning",
             "This document exceeds 100,000 characters. Live preview updates may become slower."),
            (1_000_000, "Extreme document size warning",
             "This document exceeds 1,000,000 characters. Previewing, copying, and exporting may take significant time."),
        )
        for threshold, title, message in thresholds:
            if count > threshold and threshold not in self.warned_char_thresholds:
                self.warned_char_thresholds.add(threshold)
                self.root.after_idle(lambda t=title, m=message, c=count:
                    messagebox.showwarning(t, f"{m}\n\nCurrent input size: {c:,} characters."))
            elif count <= threshold:
                self.warned_char_thresholds.discard(threshold)

    def refresh(self):
        self.check_character_warnings()
        had_content = self.preview.compare("end-1c", ">", "1.0")
        old_yview = self.preview.yview()
        old_xview = self.preview.xview()
        top_index = self.preview.index("@0,0")
        was_at_bottom = bool(had_content and old_yview and old_yview[1] >= 0.999)
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", self.result())
        self.preview.configure(state="disabled")
        if was_at_bottom:
            self.preview.yview_moveto(1.0)
        else:
            self.preview.yview(top_index)
        if old_xview:
            self.preview.xview_moveto(old_xview[0])
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
