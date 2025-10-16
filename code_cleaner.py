# code_cleaner.py
import tkinter as tk
from tkinter import filedialog, messagebox
import re
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import sys

# Optional formatter
try:
    import autopep8
    HAS_AUTOPEP8 = True
except Exception:
    HAS_AUTOPEP8 = False

class CodeCleanerApp:
    def __init__(self, root):
        self.root = root
        root.title("Code Cleaner")
        root.geometry("1000x700")
        root.minsize(800, 500)

        # Set window icon if you have one (optional)
        # icon_path = os.path.join(os.path.dirname(__file__), "clean.ico")
        # if os.path.exists(icon_path):
        #     try:
        #         root.iconbitmap(icon_path)
        #     except Exception:
        #         pass

        # Top frame: options + buttons
        top_frame = ttk.Frame(root, padding=(12,10))
        top_frame.pack(side=tk.TOP, fill=tk.X)

        # Left: options grouped in a frame (gives cleaner layout)
        options_frame = ttk.Frame(top_frame)
        options_frame.pack(side=tk.LEFT, anchor="w")

        self.remove_comments_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Remove full-line comments (#...)", variable=self.remove_comments_var).grid(row=0, column=0, padx=6, pady=2, sticky="w")

        self.trim_trailing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Trim trailing whitespace", variable=self.trim_trailing_var).grid(row=0, column=1, padx=6, pady=2, sticky="w")

        self.collapse_blank_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Collapse multiple blank lines", variable=self.collapse_blank_var).grid(row=0, column=2, padx=6, pady=2, sticky="w")

        if HAS_AUTOPEP8:
            self.use_autopep8_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(options_frame, text="Format with autopep8 (if enabled)", variable=self.use_autopep8_var).grid(row=0, column=3, padx=6, pady=2, sticky="w")
        else:
            ttk.Label(options_frame, text="(autopep8 not installed)").grid(row=0, column=3, padx=6, pady=2, sticky="w")

        # Right: action buttons
        buttons_frame = ttk.Frame(top_frame)
        buttons_frame.pack(side=tk.RIGHT, anchor="e")

        ttk.Button(buttons_frame, text="Swap Input/Output", command=self.swap_io, bootstyle="outline-info").grid(row=0, column=0, padx=6)
        ttk.Button(buttons_frame, text="Clean Code ▶", command=self.clean_code, bootstyle="success").grid(row=0, column=1, padx=6)

        # Paned windows for input / output (vertical split)
        paned = ttk.PanedWindow(root, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=(6,0))

        # Input frame (card-like)
        input_frame = ttk.Labelframe(paned, text="Input Code", padding=(8,8))
        input_frame.pack(fill=tk.BOTH, expand=True)
        paned.add(input_frame, weight=1)

        # Use Text inside a plain frame so we can style scrollbars
        self.input_text = tk.Text(input_frame, wrap="none", undo=True, bg="#ffffff", relief="flat", padx=8, pady=6)
        self._add_scrollbars(input_frame, self.input_text)

        # Output frame
        output_frame = ttk.Labelframe(paned, text="Cleaned Output", padding=(8,8))
        output_frame.pack(fill=tk.BOTH, expand=True)
        paned.add(output_frame, weight=1)

        self.output_text = tk.Text(output_frame, wrap="none", undo=True, bg="#ffffff", relief="flat", padx=8, pady=6)
        self._add_scrollbars(output_frame, self.output_text)

        # Status bar with progress and text
        status_frame = ttk.Frame(root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status = tk.StringVar(value="Ready")
        statusbar = ttk.Label(status_frame, textvariable=self.status, anchor=tk.W)
        statusbar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6,0), pady=4)

        self.progress = ttk.Progressbar(status_frame, length=140, mode="determinate")
        self.progress.pack(side=tk.RIGHT, padx=6, pady=4)

        # Menu
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        filemenu.add_command(label="Save As...", command=self.save_file, accelerator="Ctrl+S")
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=helpmenu)

        root.config(menu=menubar)

        # Bindings: shortcuts and cursor position update
        root.bind("<Control-o>", lambda e: self.open_file())
        root.bind("<Control-s>", lambda e: self.save_file())
        root.bind("<Control-e>", lambda e: self.clean_code())
        self.input_text.bind("<KeyRelease>", self.update_cursor_position)
        self.input_text.bind("<ButtonRelease>", self.update_cursor_position)

    def _add_scrollbars(self, parent, text_widget):
        vscroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=text_widget.yview)
        hscroll = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=text_widget.xview)
        text_widget.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        text_widget.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns", padx=(4,0))
        hscroll.grid(row=1, column=0, sticky="ew", pady=(4,0))
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert(tk.END, data)
            self.status.set(f"Opened: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def save_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if not path:
            return
        try:
            data = self.output_text.get("1.0", tk.END)
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
            self.status.set(f"Saved: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")

    def swap_io(self):
        in_txt = self.input_text.get("1.0", tk.END)
        out_txt = self.output_text.get("1.0", tk.END)
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert(tk.END, out_txt)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, in_txt)
        self.status.set("Swapped input and output")

    def clean_code(self):
        raw = self.input_text.get("1.0", tk.END)
        self.status.set("Cleaning...")
        self.root.update_idletasks()
        self.progress.start(10)

        cleaned = raw.splitlines()

        # 1) Trim trailing whitespace
        if self.trim_trailing_var.get():
            cleaned = [line.rstrip() for line in cleaned]

        # 2) Remove full-line comments (lines starting with optional spaces then #)
        if self.remove_comments_var.get():
            new_lines = []
            for line in cleaned:
                if re.match(r'^\s*#', line):
                    # skip full-line comment
                    continue
                new_lines.append(line)
            cleaned = new_lines

        # 3) Collapse multiple blank lines into a single blank line
        if self.collapse_blank_var.get():
            new_lines = []
            blank_count = 0
            for line in cleaned:
                if line.strip() == "":
                    blank_count += 1
                else:
                    blank_count = 0
                if blank_count <= 1:
                    new_lines.append(line)
            cleaned = new_lines

        result = "\n".join(cleaned).rstrip() + "\n"

        # 4) Optionally run autopep8 if available and checked
        if HAS_AUTOPEP8 and getattr(self, "use_autopep8_var", None) and self.use_autopep8_var.get():
            try:
                result = autopep8.fix_code(result)
                self.status.set("Cleaned + formatted with autopep8")
            except Exception:
                self.status.set("Cleaned (autopep8 failed)")
        else:
            self.status.set("Cleaned")

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, result)

        self.progress.stop()

    def update_cursor_position(self, event=None):
        try:
            idx = self.input_text.index(tk.INSERT)
            line, col = idx.split('.')
            self.status.set(f"Line {line}, Col {col}")
        except Exception:
            pass

    def show_about(self):
        messagebox.showinfo("About", "Code Cleaner\nModernized with ttkbootstrap\nBy You")

def main():
    # Use a ttkbootstrap themed window: choose a theme you like ("minty", "flatly", "darkly", "cyborg")
    root = ttk.Window(themename="minty")
    app = CodeCleanerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
