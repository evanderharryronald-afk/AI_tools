import os
import json
import fnmatch
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import TkinterDnD

# =================== Config ===================
CONFIG_PATH = "merge_tool_config.json"

DEFAULT_CONFIG = {
    "ignore_rules": {
        ".git": True,
        "__pycache__": True,
        ".venv": True,
        "*.pyc": True,
        "*.pyo": True,
    }
}

SUPPORTED_EXTS = {".py", ".md", ".txt"}

# =================== Helper ===================
def merge_files_with_relative_paths(files, root_dir):
    merged_code = []
    for file in files:
        rel = os.path.relpath(file, root_dir).replace("\\", "/")
        merged_code.append(f"# ===== File: {rel} =====\n")
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            merged_code.append(f.read().rstrip() + "\n\n")
    return merged_code


def save_merged_code(merged_code):
    save_path = filedialog.asksaveasfilename(
        title="Save merged file",
        defaultextension=".txt",
        initialfile="merged_code.txt",
        filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py")]
    )
    if save_path:
        with open(save_path, "w", encoding="utf-8") as f:
            f.writelines(merged_code)
        messagebox.showinfo("Done", f"Merged file saved:\n{save_path}")

# =================== GUI ===================
class MergeToolTreeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Merge Tool (TreeView)")
        self.root.geometry("900x600")
        self.root.configure(bg="#f7f7f7")

        self.root_dir = None
        self.selected_files = []

        self.config = self.load_config()
        self.ignore_rules = self.config.get("ignore_rules", DEFAULT_CONFIG["ignore_rules"].copy())

        # ================= Top =================
        top_frame = tk.Frame(root, bg="#f7f7f7")
        top_frame.pack(fill="x", padx=10, pady=10)

        self.root_label = tk.Label(
            top_frame,
            text="Root Directory: Not selected",
            bg="#f7f7f7",
            font=("Arial", 12),
            anchor="w"
        )
        self.root_label.pack(side="left", fill="x", expand=True)

        tk.Button(
            top_frame,
            text="Select Root Directory",
            command=self.select_root_directory,
            bg="#2196F3",
            fg="white"
        ).pack(side="right", padx=5)

        tk.Button(
            top_frame,
            text="Filter Settings",
            command=self.open_filter_settings,
            bg="#607D8B",
            fg="white"
        ).pack(side="right", padx=5)

        # ================= Middle =================
        paned = tk.PanedWindow(root, orient="horizontal", sashrelief="sunken")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        tree_frame = tk.Frame(paned, bg="#f7f7f7")
        self.tree = ttk.Treeview(tree_frame)
        self.tree.pack(fill="both", expand=True, side="left")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=scroll.set)

        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_expand)

        paned.add(tree_frame)

        list_frame = tk.Frame(paned, bg="#f7f7f7")
        self.listbox = tk.Listbox(list_frame, font=("Consolas", 11))
        self.listbox.pack(fill="both", expand=True, side="left")

        lscroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        lscroll.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=lscroll.set)

        self.listbox.bind("<<ListboxSelect>>", self.on_list_select)

        paned.add(list_frame)

        # ================= Bottom =================
        self.count_label = tk.Label(
            root,
            text="Selected files: 0",
            bg="#f7f7f7",
            font=("Arial", 11)
        )
        self.count_label.pack(pady=(0, 5))

        bottom = tk.Frame(root, bg="#f7f7f7")
        bottom.pack(fill="x", padx=10, pady=10)

        tk.Button(bottom, text="Remove Selected",
                  command=self.remove_selected,
                  bg="#FF9800", fg="white").pack(side="left", padx=5)

        tk.Button(bottom, text="Clear All",
                  command=self.clear_all,
                  bg="#f44336", fg="white").pack(side="left", padx=5)

        tk.Button(bottom, text="Merge Now",
                  command=self.merge_now,
                  bg="#673AB7", fg="white").pack(side="right", padx=5)

    # ================= Config =================
    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "ignore_rules" not in data:
                        data["ignore_rules"] = DEFAULT_CONFIG["ignore_rules"].copy()
                    return data
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        self.config["ignore_rules"] = self.ignore_rules
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def should_ignore(self, name):
        for rule, enabled in self.ignore_rules.items():
            if enabled and fnmatch.fnmatch(name, rule):
                return True
        return False

    # ================= Tree =================
    def select_root_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.root_dir = os.path.abspath(path)
            self.root_label.config(text=f"Root Directory: {self.root_dir}")
            self.populate_tree()

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        if not self.root_dir:
            return  # 安全判断
        root_node = self.tree.insert(
            "",
            "end",
            text=os.path.basename(self.root_dir),
            values=[self.root_dir],
            open=False
        )
        self.tree.insert(root_node, "end")  # dummy

    def insert_children(self, parent, path):
        entries = []
        for name in os.listdir(path):
            abs_path = os.path.join(path, name)
            if self.should_ignore(name):
                continue
            if os.path.isdir(abs_path) or os.path.splitext(name)[1] in SUPPORTED_EXTS:
                entries.append((name, abs_path))
        entries.sort(key=lambda x: (0 if os.path.isdir(x[1]) else 1, x[0].lower()))
        for name, abs_path in entries:
            node = self.tree.insert(parent, "end", text=name, values=[abs_path])
            if os.path.isdir(abs_path):
                self.tree.insert(node, "end")  # dummy

    def on_tree_expand(self, event):
        node = self.tree.selection()[0]
        self.tree.delete(*self.tree.get_children(node))
        path = self.tree.item(node, "values")[0]
        if os.path.isdir(path):
            self.insert_children(node, path)

    def on_tree_double_click(self, event):
        node = self.tree.focus()
        path = self.tree.item(node, "values")[0]
        if os.path.isfile(path) and path not in self.selected_files:
            self.selected_files.append(path)
            self.refresh_listbox()

    # ================= List =================
    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for f in self.selected_files:
            self.listbox.insert(tk.END, os.path.relpath(f, self.root_dir))
        self.count_label.config(text=f"Selected files: {len(self.selected_files)}")

    def on_list_select(self, event):
        if not self.listbox.curselection():
            return
        idx = self.listbox.curselection()[0]
        path = self.selected_files[idx]
        self.highlight_in_tree(path)

    def highlight_in_tree(self, target):
        for item in self.tree.get_children():
            if self._search_tree(item, target):
                break

    def _search_tree(self, node, target):
        if self.tree.item(node, "values")[0] == target:
            self.tree.selection_set(node)
            self.tree.see(node)
            return True
        for child in self.tree.get_children(node):
            if self._search_tree(child, target):
                return True
        return False

    def remove_selected(self):
        for i in reversed(self.listbox.curselection()):
            self.selected_files.pop(i)
        self.refresh_listbox()

    def clear_all(self):
        self.selected_files.clear()
        self.refresh_listbox()

    def merge_now(self):
        if not self.root_dir or not self.selected_files:
            messagebox.showwarning("Warning", "Root directory or files not selected.")
            return
        merged = merge_files_with_relative_paths(self.selected_files, self.root_dir)
        save_merged_code(merged)

    # ================= Filter Settings =================
    def open_filter_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Filter Settings")
        win.geometry("420x300")
        win.configure(bg="#f7f7f7")

        container = tk.Frame(win, bg="#f7f7f7")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        vars_map = {}

        for rule, enabled in self.ignore_rules.items():
            var = tk.BooleanVar(value=enabled)
            vars_map[rule] = var
            tk.Checkbutton(
                container,
                text=rule,
                variable=var,
                bg="#f7f7f7",
                command=lambda r=rule, v=var: self.toggle_rule(r, v)
            ).pack(anchor="w")

        ttk.Separator(container).pack(fill="x", pady=6)

        new_var = tk.StringVar()
        entry = tk.Entry(container, textvariable=new_var)
        entry.pack(fill="x")

        def add_rule():
            rule = new_var.get().strip()
            if rule and rule not in self.ignore_rules:
                self.ignore_rules[rule] = True
                self.save_config()
                win.destroy()
                if self.root_dir:  # 只有选了根目录才刷新 Tree
                    self.populate_tree()

        tk.Button(container, text="Add Rule", command=add_rule).pack(pady=6)

    def toggle_rule(self, rule, var):
        self.ignore_rules[rule] = var.get()
        self.save_config()
        if self.root_dir:
            self.populate_tree()


# =================== Run ===================
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    MergeToolTreeApp(root)
    root.mainloop()
