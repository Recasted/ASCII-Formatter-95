import os
import textwrap
import tkinter as tk
from tkinter import filedialog, messagebox


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
}


def ascii_title(value):
    value = "".join(c for c in value.upper() if c in FONT)[:16] or "UNTITLED"
    return "\n".join(" ".join(FONT[c][row] for c in value).rstrip() for row in range(5))


def make_document(title, info, explanation, reason, width=82):
    inner = width - 4
    def centered(value=""):
        return f"| {value[:inner].center(inner)} |"
    def body(value):
        value = value.strip() or "(none provided)"
        lines = []
        for paragraph in value.splitlines() or [""]:
            wrapped = textwrap.wrap(paragraph, inner, replace_whitespace=False) or [""]
            lines.extend(f"| {line.ljust(inner)} |" for line in wrapped)
        return lines
    border = "+" + "-" * (width - 2) + "+"
    rule = "+" + "=" * (width - 2) + "+"
    art = ascii_title(title)
    lines = [border]
    for line in art.splitlines():
        lines.append(centered(line))
    lines += [rule]
    for label, value in (("INFORMATION", info), ("EXPLANATION", explanation), ("REASON", reason)):
        lines += [centered(f"[ {label} ]"), centered()]
        lines += body(value)
        lines += [centered(), rule]
    lines += [centered("Generated with ASCII Formatter 95"), border]
    return "\n".join(lines)


class RaisedButton(tk.Button):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, fg=BLACK, activebackground=BG,
                         relief="raised", bd=3, font=("MS Sans Serif", 9, "bold"),
                         padx=12, pady=3, **kwargs)


class App:
    def __init__(self, root):
        self.root = root
        root.title("ASCII Formatter 95")
        root.geometry("1120x720")
        root.minsize(850, 560)
        root.configure(bg=BG)

        titlebar = tk.Frame(root, bg=BLUE, bd=2, relief="raised")
        titlebar.pack(fill="x", padx=4, pady=(4, 0))
        tk.Label(titlebar, text="▣  ASCII Formatter 95", bg=BLUE, fg=WHITE,
                 font=("MS Sans Serif", 10, "bold"), anchor="w").pack(side="left", fill="x", expand=True, padx=5, pady=3)
        tk.Label(titlebar, text="?", width=3, bg=BG, relief="raised", bd=2).pack(side="right", padx=2, pady=2)

        toolbar = tk.Frame(root, bg=BG, bd=2, relief="raised")
        toolbar.pack(fill="x", padx=4)
        for text in ("File", "Edit", "Format", "Help"):
            tk.Label(toolbar, text=text, bg=BG, padx=8, pady=3).pack(side="left")

        main = tk.PanedWindow(root, orient="horizontal", bg=BG, sashwidth=7, bd=2, relief="sunken")
        main.pack(fill="both", expand=True, padx=7, pady=7)
        left = tk.Frame(main, bg=BG, width=310, bd=2, relief="raised")
        right = tk.Frame(main, bg=BG, bd=2, relief="sunken")
        main.add(left, minsize=270)
        main.add(right, minsize=500)

        tk.Label(left, text="Document fields", bg=BLUE, fg=WHITE,
                 font=("MS Sans Serif", 9, "bold"), anchor="w").pack(fill="x", padx=4, pady=4)
        self.title = self.field(left, "Title", one_line=True)
        self.info = self.field(left, "Information")
        self.explanation = self.field(left, "Explanation")
        self.reason = self.field(left, "Reason")

        options = tk.LabelFrame(left, text="Options", bg=BG, font=("MS Sans Serif", 9))
        options.pack(fill="x", padx=8, pady=6)
        tk.Label(options, text="Output width:", bg=BG).pack(side="left", padx=5, pady=6)
        self.width = tk.Spinbox(options, from_=64, to=120, width=5, relief="sunken", bd=2, command=self.refresh)
        self.width.delete(0, "end"); self.width.insert(0, "82")
        self.width.pack(side="left")

        buttons = tk.Frame(left, bg=BG)
        buttons.pack(fill="x", padx=7, pady=7)
        RaisedButton(buttons, text="Preview", command=self.refresh).pack(side="left", padx=2)
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

        self.status = tk.Label(root, text="Ready", bg=BG, bd=2, relief="sunken", anchor="w")
        self.status.pack(fill="x", padx=5, pady=(0, 5))
        self.title.insert(0, "MY REPORT")
        for widget in (self.title, self.info, self.explanation, self.reason):
            widget.bind("<KeyRelease>", lambda _e: self.refresh())
        self.refresh()

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
        try: width = max(64, min(120, int(self.width.get())))
        except ValueError: width = 82
        return make_document(self.value(self.title), self.value(self.info),
                             self.value(self.explanation), self.value(self.reason), width)

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
