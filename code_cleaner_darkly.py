# Standard library imports
import ast
import re
from tkinter import filedialog, messagebox

# Third party imports
import requests
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

def send_to_backend(self):
    cleaned_code = self.output_text.get("1.0", "end-1c")
    if not cleaned_code.strip():
        messagebox.showwarning("Warning", "No cleaned code to send!")
        return

    try:
        response = requests.post(
            "http://127.0.0.1:8000/upload_code/",
            json={"cleaned_code": cleaned_code},
            timeout=5
        )

        if response.status_code == 200:
            res = response.json()
            messagebox.showinfo("Success", f"✅ {res['message']}")
            self.status.config(text="Cleaned code sent to backend ✅")
        else:
            messagebox.showerror("Error", f"Backend error: {response.text}")
            self.status.config(text="Backend returned an error ❌")

    except Exception as e:
        messagebox.showerror("Connection Error", str(e))
        self.status.config(text="Failed to send to backend ❌")


try:
    import isort  
    isort_api = getattr(isort, "api", isort)

    def sort_code_with_isort(code: str) -> str:
        try:
            if hasattr(isort_api, "sort_code_string"):
                return isort_api.sort_code_string(code)
            if hasattr(isort_api, "sort_code"):
                return isort_api.sort_code(code)
            if hasattr(isort_api, "code"):
                return isort_api.code(code)
            if hasattr(isort, "sort_code_string"):
                return isort.sort_code_string(code)
            if hasattr(isort, "sort_code"):
                return isort.sort_code(code)
        except Exception:
            return code
        return code

    HAS_ISORT = True
except ImportError:
    isort_api = None

    def sort_code_with_isort(code: str) -> str:
        return code
    HAS_ISORT = False

try:
    import autopep8
    HAS_AUTOPEP8 = True
except ImportError:
    autopep8 = None
    HAS_AUTOPEP8 = False
    print("Warning: autopep8 not installed. Code formatting will be disabled.")


class CodeCleanerApp:
    def __init__(self, app, backend_url="http://127.0.0.1:8000"):
        self.backend_url = backend_url
        self.app = app
        self.app.title("Python Code Cleaner - Dark Mode")
        self.app.geometry("1000x700")

        self.text_bg = "#1e1e1e"
        self.text_fg = "#f5f5f5"
        self.text_font = ("Consolas", 12)

        self.remove_comments = ttk.BooleanVar(value=True)
        self.trim_whitespace = ttk.BooleanVar(value=True)
        self.collapse_blank_lines = ttk.BooleanVar(value=True)
        self.format_code = ttk.BooleanVar(value=False)
        self.sort_imports = ttk.BooleanVar(value=False)

        top_frame = ttk.Frame(self.app, padding=8)
        top_frame.pack(side=TOP, fill=X)

        ttk.Label(top_frame, text="Options:",
                  bootstyle="inverse-secondary").pack(side=LEFT, padx=5)

        ttk.Checkbutton(top_frame, text="Remove full-line comments", variable=self.remove_comments,
                        bootstyle="round-toggle").pack(side=LEFT, padx=5)
        ttk.Checkbutton(top_frame, text="Trim trailing whitespace", variable=self.trim_whitespace,
                        bootstyle="round-toggle").pack(side=LEFT, padx=5)
        ttk.Checkbutton(top_frame, text="Collapse blank lines", variable=self.collapse_blank_lines,
                        bootstyle="round-toggle").pack(side=LEFT, padx=5)

        if HAS_AUTOPEP8:
            ttk.Checkbutton(top_frame, text="Format with autopep8", variable=self.format_code,
                            bootstyle="round-toggle").pack(side=LEFT, padx=5)
        else:
            ttk.Label(top_frame, text="(autopep8 not installed)",
                      foreground="#ff8080").pack(side=LEFT, padx=10)

        if HAS_ISORT:
            ttk.Checkbutton(top_frame, text="Sort imports (isort)", variable=self.sort_imports,
                            bootstyle="round-toggle").pack(side=LEFT, padx=5)

        ttk.Button(top_frame, text="Clean Code ▶", command=self.clean_code,
                   bootstyle="success-outline").pack(side=LEFT, padx=10)
        ttk.Button(top_frame, text="Swap Input/Output", command=self.swap_text,
                   bootstyle="info-outline").pack(side=LEFT, padx=5)
        ttk.Button(top_frame, text="Validate Syntax", command=self.validate_syntax,
                   bootstyle="warning-outline").pack(side=LEFT, padx=5)
        ttk.Button(top_frame, text="Copy Output", command=self.copy_output,
                   bootstyle="secondary-outline").pack(side=LEFT, padx=5)
        ttk.Button(top_frame, text="Send to Backend", 
                   command=self.send_to_backend,
                   bootstyle="primary-outline").pack(side=LEFT, padx=5)

        pw = ttk.PanedWindow(self.app, orient="vertical")
        pw.pack(fill=BOTH, expand=TRUE, padx=10, pady=5)

        input_frame = ttk.Labelframe(pw, text="Input Code", bootstyle="dark")
        self.input_text = ttk.Text(input_frame, wrap="none", undo=True, font=self.text_font,
                                   background=self.text_bg, foreground=self.text_fg,
                                   insertbackground="white", height=15)
        self.input_text.pack(fill=BOTH, expand=TRUE)
        pw.add(input_frame)

        output_frame = ttk.Labelframe(
            pw, text="Cleaned Output", bootstyle="dark")
        self.output_text = ttk.Text(output_frame, wrap="none", undo=True, font=self.text_font,
                                    background=self.text_bg, foreground=self.text_fg,
                                    insertbackground="white", height=15)
        self.output_text.pack(fill=BOTH, expand=TRUE)
        pw.add(output_frame)

        menubar = ttk.Menu(self.app, background="#2b2b2b",
                           foreground="#f5f5f5", activebackground="#3b3b3b")
        file_menu = ttk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open File", command=self.open_file)
        file_menu.add_command(label="Save Cleaned Output",
                              command=self.save_output)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.app.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.app.config(menu=menubar)

        self.status = ttk.Label(self.app, text="Ready",
                                anchor=W, bootstyle="inverse-dark")
        self.status.pack(side=BOTTOM, fill=X)

        self.app.bind("<Control-o>", lambda e: self.open_file())
        self.app.bind("<Control-s>", lambda e: self.save_output())
        self.app.bind("<Control-e>", lambda e: self.clean_code())

    def clean_code(self):
        code = self.input_text.get("1.0", "end-1c")
        original_lines = code.splitlines()
        lines = original_lines.copy()
        cleaned = []

        if self.trim_whitespace.get():
            lines = [line.rstrip() for line in lines]

        comments_before = sum(1 for l in lines if re.match(r'^\s*#', l))
        if self.remove_comments.get():
            lines = [line for line in lines if not re.match(r'^\s*#', line)]

        if self.collapse_blank_lines.get():
            blank_count = 0
            new_lines = []
            for line in lines:
                if line.strip() == "":
                    blank_count += 1
                else:
                    blank_count = 0
                if blank_count <= 1:
                    new_lines.append(line)
            lines = new_lines

        cleaned = "\n".join(lines)

        if HAS_AUTOPEP8 and self.format_code.get():
            cleaned = autopep8.fix_code(cleaned)

        if HAS_ISORT and self.sort_imports.get():
            try:
                cleaned = sort_code_with_isort(cleaned)
            except Exception:
                pass

        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", cleaned)

        cleaned_lines = cleaned.splitlines()
        removed_comments = comments_before - \
            sum(1 for l in cleaned_lines if re.match(r'^\s*#', l))
        stats = f"Lines: {len(original_lines)} → {len(cleaned_lines)} | Comments removed: {max(0, removed_comments)}"
        self.status.config(text=f"Code cleaned successfully  — {stats}")

    def swap_text(self):
        input_content = self.input_text.get("1.0", "end-1c")
        output_content = self.output_text.get("1.0", "end-1c")
        self.input_text.delete("1.0", "end")
        self.output_text.delete("1.0", "end")
        self.input_text.insert("1.0", output_content)
        self.output_text.insert("1.0", input_content)
        self.status.config(text="Input and Output swapped ")

    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", content)
            self.status.config(text=f"Opened file: {path}")

    def save_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".py",
                                            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.output_text.get("1.0", "end-1c"))
            self.status.config(text=f"Output saved to: {path}")
            messagebox.showinfo("Saved", f"Output saved to:\n{path}")

    def copy_output(self):
        out = self.output_text.get("1.0", "end-1c")
        if out:
            try:
                self.app.clipboard_clear()
                self.app.clipboard_append(out)
                self.status.config(text="Output copied to clipboard 📋")
            except Exception:
                self.status.config(text="Failed to copy to clipboard")

    def validate_syntax(self):
        code = self.output_text.get(
            "1.0", "end-1c") or self.input_text.get("1.0", "end-1c")
        try:
            ast.parse(code)
            messagebox.showinfo("Syntax Check", "No syntax errors found ")
            self.status.config(text="Syntax valid ")
        except SyntaxError as e:
            messagebox.showerror(
                "Syntax Error", f"SyntaxError: {e.msg}\nLine: {e.lineno}, Offset: {e.offset}")
            self.status.config(text=f"Syntax error at line {e.lineno} ")


if __name__ == "__main__":
    app = ttk.Window(themename="darkly")
    CodeCleanerApp(app)
    app.mainloop()