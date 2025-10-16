import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import autopep8
    HAS_AUTOPEP8 = True
except Exception:
    HAS_AUTOPEP8 = False


class CodeCleanerApp:
    def __init__(self, root):
        self.root = root
        root.title("Code Cleaner")
        root.geometry("900x700")

        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open...", command=self.open_file)
        filemenu.add_command(label="Save As...", command=self.save_file)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        root.config(menu=menubar)

        top_frame = ttk.Frame(root, padding=(8, 6))
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self.remove_comments_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top_frame, text="Remove full-line comments (#...)",
                        variable=self.remove_comments_var).pack(side=tk.LEFT, padx=6)

        self.trim_trailing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(top_frame, text="Trim trailing whitespace",
                        variable=self.trim_trailing_var).pack(side=tk.LEFT, padx=6)

        self.collapse_blank_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(top_frame, text="Collapse multiple blank lines",
                        variable=self.collapse_blank_var).pack(side=tk.LEFT, padx=6)

        if HAS_AUTOPEP8:
            self.use_autopep8_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(top_frame, text="Format with autopep8 (if enabled)",
                            variable=self.use_autopep8_var).pack(side=tk.LEFT, padx=6)
        else:
            ttk.Label(top_frame, text="(autopep8 not installed)").pack(
                side=tk.LEFT, padx=6)

        ttk.Button(top_frame, text="Clean Code ▶",
                   command=self.clean_code).pack(side=tk.RIGHT, padx=6)
        ttk.Button(top_frame, text="Swap Input/Output",
                   command=self.swap_io).pack(side=tk.RIGHT, padx=6)

        paned = ttk.Panedwindow(root, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        input_frame = ttk.Labelframe(paned, text="Input Code", padding=(6, 6))
        self.input_text = tk.Text(input_frame, wrap="none", undo=True)
        self._add_scrollbars(input_frame, self.input_text)
        input_frame.pack(fill=tk.BOTH, expand=True)
        paned.add(input_frame, weight=1)

        output_frame = ttk.Labelframe(
            paned, text="Cleaned Output", padding=(6, 6))
        self.output_text = tk.Text(
            output_frame, wrap="none", undo=True, state=tk.NORMAL)
        self._add_scrollbars(output_frame, self.output_text)
        output_frame.pack(fill=tk.BOTH, expand=True)
        paned.add(output_frame, weight=1)

        self.status = tk.StringVar(value="Ready")
        statusbar = ttk.Label(root, textvariable=self.status,
                              relief=tk.SUNKEN, anchor=tk.W)
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def _add_scrollbars(self, parent, text_widget):
        vscroll = ttk.Scrollbar(
            parent, orient=tk.VERTICAL, command=text_widget.yview)
        hscroll = ttk.Scrollbar(
            parent, orient=tk.HORIZONTAL, command=text_widget.xview)
        text_widget.configure(yscrollcommand=vscroll.set,
                              xscrollcommand=hscroll.set)
        text_widget.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll.grid(row=1, column=0, sticky="ew")
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert(tk.END, data)
            self.status.set(f"Opened: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def save_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[
                                            ("Python files", "*.py"), ("All files", "*.*")])
        if not path:
            return
        try:
            data = self.output_text.get("1.0", tk.END)
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
            self.status.set(f"Saved: {path}")
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

        cleaned = raw.splitlines()

        if self.trim_trailing_var.get():
            cleaned = [line.rstrip() for line in cleaned]

        if self.remove_comments_var.get():
            new_lines = []
            for line in cleaned:
                if re.match(r'^\s*#', line):
                    continue
                new_lines.append(line)
            cleaned = new_lines

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

        if HAS_AUTOPEP8 and getattr(self, "use_autopep8_var", None) and self.use_autopep8_var.get():
            try:
                result = autopep8.fix_code(result)
                self.status.set("Cleaned + formatted with autopep8")
            except Exception as e:
                self.status.set("Cleaned (autopep8 failed)")
        else:
            self.status.set("Cleaned")

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, result)


def main():
    root = tk.Tk()
    app = CodeCleanerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

