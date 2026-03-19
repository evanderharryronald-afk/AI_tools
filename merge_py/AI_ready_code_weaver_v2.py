# AI_tools/merge_py/AI_ready_code_weaver_v2.py
"""
================================================================================
PROJECT NAME: AI-Ready Code Weaver (v2.0 - Structure Enhanced)
DESCRIPTION:
    在 v1.0 交互基准上的深度增强版。核心目标是为 LLM (如 Claude 3.5, GPT-4)
    提供更高质量的代码上下文。不仅合并代码，更“编织”项目逻辑。

WHAT'S NEW IN V2.0 (vs v1.0):
    1.  [智能目录树生成]：新增 ASCII 树形逻辑。合并时自动在头部注入项目结构，
        让 AI 瞬间理解文件间的层级关系。
    2.  [独立结构输出]：新增 "Export Tree Only" 功能。支持单独导出所选文件的
        .md 格式目录树，适用于项目文档快速生成。
    3.  [工业级后缀支持]：大幅扩展文件识别范围。
        - 配置文件：.json, .yaml, .yml, .env
        - 容器/运维：Dockerfile, .sh, .bat
        - 数据库/前端：.sql, .css, .js
    4.  [布局优化]：右下角操作区双按钮设计，区分“纯结构输出”与“带结构合并”。

CORE PHILOSOPHY:
    V1 是为了“选得快”，V2 是为了“喂得好”。
    通过在代码前置入结构树，可有效降低 AI 理解大型复杂项目时的 Token 损耗和幻觉率。

AUTHOR: Evander
DATE: 2026-03-19
VERSION: 2.0.0 - AI Context Optimized
================================================================================
"""

import os
import json
import fnmatch
import re
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
        ".idea": True,
        "node_modules": True,
        "*.pyc": True,
        "*.pyo": True,
    }
}

# 1. 扩展支持的文件类型
SUPPORTED_EXTS = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".sql", ".sh", ".bat", ".xml", ".css", ".js"}
SUPPORTED_NAMES = {"Dockerfile", "requirements.txt", ".env"}


# =================== 核心逻辑：目录树生成 ===================
def generate_ascii_tree(files, root_dir):
    """根据选中的文件列表生成 ASCII 树"""
    if not files: return ""
    tree_lines = ["# Project Structure\n", "```"]

    paths = [os.path.relpath(f, root_dir).split(os.sep) for f in files]
    tree = {}
    for path_parts in paths:
        current = tree
        for part in path_parts:
            current = current.setdefault(part, {})

    def _recurse(node, prefix=""):
        items = sorted(node.keys(), key=lambda x: (len(node[x]) == 0, x.lower()))
        for i, name in enumerate(items):
            is_last = (i == len(items) - 1)
            connector = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{connector}{name}")
            if node[name]:
                _recurse(node[name], prefix + ("    " if is_last else "│   "))

    _recurse(tree)
    tree_lines.append("```\n\n")
    return "\n".join(tree_lines)


# =================== Helper ===================
def merge_files_with_relative_paths(files, root_dir, include_tree=True):
    merged_code = []
    # 如果勾选或需要，先加树
    if include_tree:
        merged_code.append(generate_ascii_tree(files, root_dir))

    for file in files:
        rel = os.path.relpath(file, root_dir).replace("\\", "/")
        merged_code.append(f"# ===== File: {rel} =====\n")
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            merged_code.append(f.read().rstrip() + "\n\n")
    return merged_code


# =================== GUI ===================
class MergeToolTreeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Merge Tool (Tree & Extended Support)")
        self.root.geometry("950x650")  # 稍微调宽一点点
        self.root.configure(bg="#f7f7f7")

        self.root_dir = None
        self.selected_files = []
        self.dragged_files = []
        self.drag_start_index = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False

        self.last_clicked = None
        self.multi_selected_items = set()

        self.config = self.load_config()
        self.ignore_rules = self.config.get("ignore_rules", DEFAULT_CONFIG["ignore_rules"].copy())

        # ================= Top =================
        top_frame = tk.Frame(root, bg="#f7f7f7")
        top_frame.pack(fill="x", padx=10, pady=10)

        self.root_label = tk.Label(top_frame, text="Root Directory: Not selected", bg="#f7f7f7", font=("Arial", 12),
                                   anchor="w")
        self.root_label.pack(side="left", fill="x", expand=True)

        tk.Button(top_frame, text="Select Root Directory", command=self.select_root_directory, bg="#2196F3",
                  fg="white").pack(side="right", padx=5)
        tk.Button(top_frame, text="Filter Settings", command=self.open_filter_settings, bg="#607D8B", fg="white").pack(
            side="right", padx=5)

        # ================= Middle =================
        paned = tk.PanedWindow(root, orient="horizontal", sashrelief="sunken")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        tree_frame = tk.Frame(paned, bg="#f7f7f7")
        tree_header = tk.Frame(tree_frame, bg="#f7f7f7")
        tree_header.pack(fill="x", pady=(0, 5))

        left_header = tk.Frame(tree_header, bg="#f7f7f7")
        left_header.pack(side="left", fill="x", expand=True)
        tk.Label(left_header, text="Directory Tree", bg="#f7f7f7", font=("Arial", 10, "bold")).pack(side="left")

        self.multi_select_label = tk.Label(left_header, text="", bg="#f7f7f7", font=("Arial", 9), fg="#666", width=20,
                                           anchor="w")
        self.multi_select_label.pack(side="left", padx=5)

        tk.Button(tree_header, text="Add Selected →", command=self.add_multi_selected_to_list, bg="#4CAF50", fg="white",
                  font=("Arial", 9), width=12).pack(side="right", padx=2)

        self.tree = ttk.Treeview(tree_frame, selectmode="extended")
        self.tree.pack(fill="both", expand=True, side="left")
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=scroll.set)

        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_expand)
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<ButtonPress-1>", self.on_tree_button_press, add='+')
        self.tree.bind("<B1-Motion>", self.on_tree_motion)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_button_release, add='+')

        paned.add(tree_frame)

        list_frame = tk.Frame(paned, bg="#f7f7f7")
        list_header = tk.Frame(list_frame, bg="#f7f7f7")
        list_header.pack(fill="x", pady=(0, 5))
        tk.Label(list_header, text="Selected Files (drag here)", bg="#f7f7f7", font=("Arial", 10, "bold")).pack(
            side="left")

        self.listbox = tk.Listbox(list_frame, font=("Consolas", 11), selectmode="extended")
        self.listbox.pack(fill="both", expand=True, side="left")
        lscroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        lscroll.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=lscroll.set)
        self.listbox.bind("<<ListboxSelect>>", self.on_list_select)

        self.listbox.drop_target_register('DND_Files', 'DND_Text')
        self.listbox.dnd_bind('<<Drop>>', self.on_drop)
        self.listbox.dnd_bind('<<DragEnter>>', self.on_drag_enter)
        self.listbox.dnd_bind('<<DragLeave>>', self.on_drag_leave)

        paned.add(list_frame)

        # ================= Bottom =================
        self.count_label = tk.Label(root, text="Selected files: 0", bg="#f7f7f7", font=("Arial", 11))
        self.count_label.pack(pady=(0, 5))

        bottom = tk.Frame(root, bg="#f7f7f7")
        bottom.pack(fill="x", padx=10, pady=10)

        tk.Button(bottom, text="Remove Selected", command=self.remove_selected, bg="#FF9800", fg="white").pack(
            side="left", padx=5)
        tk.Button(bottom, text="Clear All", command=self.clear_all, bg="#f44336", fg="white").pack(side="left", padx=5)

        # 这里增加单独输出目录树的按钮
        tk.Button(bottom, text="Export Tree Only", command=self.export_tree_only, bg="#00BCD4", fg="white").pack(
            side="right", padx=5)
        tk.Button(bottom, text="Merge Now (with Tree)", command=self.merge_now, bg="#673AB7", fg="white",
                  font=("Arial", 10, "bold")).pack(side="right", padx=5)

    # =================== 原有配置逻辑 (保留) ===================
    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "ignore_rules" not in data: data["ignore_rules"] = DEFAULT_CONFIG["ignore_rules"].copy()
                    return data
            except:
                pass
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        self.config["ignore_rules"] = self.ignore_rules
        with open(CONFIG_PATH, "w", encoding="utf-8") as f: json.dump(self.config, f, indent=2)

    def should_ignore(self, name):
        for rule, enabled in self.ignore_rules.items():
            if enabled and fnmatch.fnmatch(name, rule): return True
        return False

    # =================== 树逻辑增强 ===================
    def select_root_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.root_dir = os.path.abspath(path)
            self.root_label.config(text=f"Root Directory: {self.root_dir}")
            self.populate_tree()

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.multi_selected_items.clear()
        self.last_clicked = None
        self.update_multi_select_label()
        if not self.root_dir: return
        root_node = self.tree.insert("", "end", text=os.path.basename(self.root_dir), values=[self.root_dir], open=True)
        self.insert_children(root_node, self.root_dir)

    def insert_children(self, parent, path):
        self.tree.delete(*self.tree.get_children(parent))
        try:
            entries = os.listdir(path)
        except:
            return

        valid_entries = []
        for name in entries:
            abs_path = os.path.join(path, name)
            if self.should_ignore(name): continue
            ext = os.path.splitext(name)[1]
            if os.path.isdir(abs_path) or ext in SUPPORTED_EXTS or name in SUPPORTED_NAMES:
                valid_entries.append((name, abs_path))

        valid_entries.sort(key=lambda x: (not os.path.isdir(x[1]), x[0].lower()))
        for name, abs_path in valid_entries:
            node = self.tree.insert(parent, "end", text=name, values=[abs_path])
            if os.path.isdir(abs_path): self.tree.insert(node, "end")

    def on_tree_expand(self, event):
        node = self.tree.focus()
        if not node: return
        path = self.tree.item(node, "values")[0]
        if os.path.isdir(path): self.insert_children(node, path)

    # =================== 原有点击和拖拽逻辑 (完全保留) ===================
    def on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "tree": return
        item = self.tree.identify_row(event.y)
        if not item: return
        values = self.tree.item(item, "values")
        if not values: return
        path = values[0]
        if not os.path.isfile(path): return
        ctrl_pressed = (event.state & 0x4) != 0
        shift_pressed = (event.state & 0x1) != 0
        if not ctrl_pressed and not shift_pressed:
            if item in self.multi_selected_items:
                self.tree.selection_set(list(self.multi_selected_items))
                return
            else:
                self.multi_selected_items = {item}
                self.last_clicked = item
        elif ctrl_pressed:
            if item in self.multi_selected_items:
                self.multi_selected_items.remove(item)
            else:
                self.multi_selected_items.add(item)
            self.last_clicked = item
        elif shift_pressed and self.last_clicked:
            self.select_range(self.last_clicked, item)
        self.tree.selection_set(list(self.multi_selected_items))
        self.update_multi_select_label()
        return "break"

    def select_range(self, start_item, end_item):
        all_files = self.get_all_file_items()
        try:
            start_idx = all_files.index(start_item)
            end_idx = all_files.index(end_item)
            if start_idx > end_idx: start_idx, end_idx = end_idx, start_idx
            for i in range(start_idx, end_idx + 1): self.multi_selected_items.add(all_files[i])
        except:
            pass

    def get_all_file_items(self, parent=""):
        result = []
        for item in self.tree.get_children(parent):
            values = self.tree.item(item, "values")
            if values and os.path.isfile(values[0]): result.append(item)
            result.extend(self.get_all_file_items(item))
        return result

    def update_multi_select_label(self):
        count = len(self.multi_selected_items)
        self.multi_select_label.config(text=f"({count} files selected)" if count > 0 else "")

    def add_multi_selected_to_list(self):
        added = 0
        for item in list(self.multi_selected_items):
            path = self.tree.item(item, "values")[0]
            if os.path.isfile(path) and path not in self.selected_files:
                self.selected_files.append(path)
                added += 1
        if added:
            self.refresh_listbox()
            self.multi_selected_items.clear()
            self.tree.selection_set([])
            self.update_multi_select_label()

    def on_tree_double_click(self, event):
        node = self.tree.focus()
        if not node: return
        val = self.tree.item(node, "values")
        if val and os.path.isfile(val[0]) and val[0] not in self.selected_files:
            self.selected_files.append(val[0])
            self.refresh_listbox()

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for f in self.selected_files:
            self.listbox.insert(tk.END, os.path.relpath(f, self.root_dir))
        self.count_label.config(text=f"Selected files: {len(self.selected_files)}")

    def on_list_select(self, event):
        if not self.listbox.curselection(): return
        idx = self.listbox.curselection()[0]
        if idx < len(self.selected_files): self.highlight_in_tree(self.selected_files[idx])

    def highlight_in_tree(self, target):
        for item in self.tree.get_children():
            if self._search_tree(item, target): break

    def _search_tree(self, node, target):
        values = self.tree.item(node, "values")
        if values and values[0] == target:
            self.tree.selection_set(node)
            self.tree.see(node)
            return True
        for child in self.tree.get_children(node):
            if self._search_tree(child, target): return True
        return False

    def remove_selected(self):
        for i in reversed(self.listbox.curselection()): self.selected_files.pop(i)
        self.refresh_listbox()

    def clear_all(self):
        self.selected_files.clear()
        self.refresh_listbox()

    # =================== 新增功能：输出逻辑 ===================
    def export_tree_only(self):
        if not self.root_dir or not self.selected_files:
            messagebox.showwarning("Warning", "Please select files to build the tree.")
            return
        tree_str = generate_ascii_tree(self.selected_files, self.root_dir)
        save_path = filedialog.asksaveasfilename(defaultextension=".md", initialfile="project_structure.md")
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f: f.write(tree_str)
            messagebox.showinfo("Done", "Project structure saved.")

    def merge_now(self):
        if not self.root_dir or not self.selected_files:
            messagebox.showwarning("Warning", "Root directory or files not selected.")
            return
        merged = merge_files_with_relative_paths(self.selected_files, self.root_dir, include_tree=True)
        save_merged_code(merged)

    # =================== 原有 Filter 窗口逻辑 (保留) ===================
    def open_filter_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Filter Settings")
        win.geometry("450x400")
        main_container = tk.Frame(win, bg="#f7f7f7")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(main_container, text="Ignore Rules:", bg="#f7f7f7", font=("Arial", 11, "bold")).pack(anchor="w")

        scroll_frame = tk.Frame(main_container, bg="#f7f7f7", relief="sunken", bd=1)
        scroll_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(scroll_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        for rule, enabled in sorted(self.ignore_rules.items()):
            rf = tk.Frame(scrollable_frame, bg="white")
            rf.pack(fill="x", padx=5, pady=2)
            v = tk.BooleanVar(value=enabled)
            tk.Checkbutton(rf, text=rule, variable=v, bg="white",
                           command=lambda r=rule, var=v: self.toggle_rule(r, var)).pack(side="left")
            if rule not in DEFAULT_CONFIG["ignore_rules"]:
                tk.Button(rf, text="✕", command=lambda r=rule, w=win: self.delete_rule(r, w), bg="#f44336", fg="white",
                          width=2).pack(side="right")

        ttk.Separator(main_container, orient="horizontal").pack(fill="x", pady=10)
        add_frame = tk.Frame(main_container, bg="#f7f7f7")
        add_frame.pack(fill="x")
        new_var = tk.StringVar()
        tk.Entry(add_frame, textvariable=new_var).pack(side="left", fill="x", expand=True, padx=5)

        def add_rule():
            r = new_var.get().strip()
            if r and r not in self.ignore_rules:
                self.ignore_rules[r] = True
                self.save_config()
                win.destroy();
                self.open_filter_settings();
                self.populate_tree()

        tk.Button(add_frame, text="Add Rule", command=add_rule, bg="#4CAF50", fg="white").pack(side="right")

    def toggle_rule(self, rule, var):
        self.ignore_rules[rule] = var.get();
        self.save_config();
        self.populate_tree()

    def delete_rule(self, rule, window):
        if messagebox.askyesno("Confirm", f"Delete rule '{rule}'?"):
            del self.ignore_rules[rule];
            self.save_config();
            window.destroy();
            self.open_filter_settings();
            self.populate_tree()

    # =================== 原有拖拽处理 (保留) ===================
    def on_tree_button_press(self, event):
        item = self.tree.identify_row(event.y)
        if item and os.path.isfile(self.tree.item(item, "values")[0]):
            self.drag_start_index, self.drag_start_x, self.drag_start_y = item, event.x, event.y
            self.is_dragging = False

    def on_tree_motion(self, event):
        if self.drag_start_index and (abs(event.x - self.drag_start_x) > 5 or abs(event.y - self.drag_start_y) > 5):
            self.is_dragging = True
            self.listbox.config(bg="#E3F2FD")

    def on_tree_button_release(self, event):
        self.listbox.config(bg="white")
        if self.is_dragging and self.drag_start_index:
            items = list(self.multi_selected_items) if self.multi_selected_items else [self.drag_start_index]
            added = 0
            for it in items:
                p = self.tree.item(it, "values")[0]
                if os.path.isfile(p) and p not in self.selected_files:
                    self.selected_files.append(p);
                    added += 1
            if added: self.refresh_listbox()
        self.drag_start_index = None;
        self.is_dragging = False

    def on_drag_enter(self, event):
        self.listbox.config(bg="#E3F2FD"); return event.action

    def on_drag_leave(self, event):
        self.listbox.config(bg="white")

    def on_drop(self, event):
        self.listbox.config(bg="white")
        data = event.data
        files = []
        if '{' in data:
            files = re.findall(r'\{([^}]+)\}', data)
        elif '\n' in data:
            files = [f.strip() for f in data.split('\n') if f.strip()]
        else:
            files = [data.strip()]

        added = 0
        for f in files:
            path = f.strip('"').strip("'").strip('{}')
            if os.path.isfile(path) and (
                    os.path.splitext(path)[1] in SUPPORTED_EXTS or os.path.basename(path) in SUPPORTED_NAMES):
                if path not in self.selected_files: self.selected_files.append(path); added += 1
        if added: self.refresh_listbox()
        return event.action


def save_merged_code(merged_code):
    path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="merged_code.txt",
                                        filetypes=[("Text", "*.txt"), ("Markdown", "*.md"), ("All", "*.*")])
    if path:
        with open(path, "w", encoding="utf-8") as f: f.writelines(merged_code)
        messagebox.showinfo("Done", f"Saved to:\n{path}")


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    MergeToolTreeApp(root)
    root.mainloop()