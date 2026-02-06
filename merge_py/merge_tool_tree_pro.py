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
        filetypes=[
            ("Text Files", "*.txt"),
            ("Python Files", "*.py"),
            ("Markdown Files", "*.md"),
            ("All Files", "*.*")
        ]
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
        self.dragged_files = []  # 用于拖拽功能
        self.drag_start_index = None  # 拖拽起始位置

        # 用于多选功能
        self.last_clicked = None
        self.multi_selected_items = set()

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

        # 左侧树形框架
        tree_frame = tk.Frame(paned, bg="#f7f7f7")

        # 树形标题和按钮
        tree_header = tk.Frame(tree_frame, bg="#f7f7f7")
        tree_header.pack(fill="x", pady=(0, 5))

        # 左侧：标题和状态
        left_header = tk.Frame(tree_header, bg="#f7f7f7")
        left_header.pack(side="left", fill="x", expand=True)

        tk.Label(left_header, text="Directory Tree", bg="#f7f7f7",
                 font=("Arial", 10, "bold")).pack(side="left")

        # 多选状态标签 - 使用固定宽度避免挤压按钮
        self.multi_select_label = tk.Label(left_header, text="", bg="#f7f7f7",
                                           font=("Arial", 9), fg="#666",
                                           width=20, anchor="w")
        self.multi_select_label.pack(side="left", padx=5)

        # 右侧：按钮 - 固定在右边不会被挤压
        tk.Button(tree_header, text="Add Selected →",
                  command=self.add_multi_selected_to_list,
                  bg="#4CAF50", fg="white",
                  font=("Arial", 9), width=12).pack(side="right", padx=2)

        # 树形控件
        self.tree = ttk.Treeview(tree_frame, selectmode="extended")
        self.tree.pack(fill="both", expand=True, side="left")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=scroll.set)

        # 绑定事件
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_expand)
        self.tree.bind("<Button-1>", self.on_tree_click)  # 单击事件用于多选

        # 【改进：拖拽功能】使用简单的拖拽实现
        self.tree.bind("<ButtonPress-1>", self.on_tree_button_press)
        self.tree.bind("<B1-Motion>", self.on_tree_motion)

        paned.add(tree_frame)

        # 右侧列表框架
        list_frame = tk.Frame(paned, bg="#f7f7f7")

        # 列表标题
        list_header = tk.Frame(list_frame, bg="#f7f7f7")
        list_header.pack(fill="x", pady=(0, 5))

        tk.Label(list_header, text="Selected Files (drag files here)", bg="#f7f7f7",
                 font=("Arial", 10, "bold")).pack(side="left")

        self.listbox = tk.Listbox(list_frame, font=("Consolas", 11), selectmode="extended")
        self.listbox.pack(fill="both", expand=True, side="left")

        lscroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        lscroll.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=lscroll.set)

        self.listbox.bind("<<ListboxSelect>>", self.on_list_select)

        # 【改进：拖拽功能】配置列表框为拖放目标
        self.listbox.drop_target_register('DND_Files', 'DND_Text')
        self.listbox.dnd_bind('<<Drop>>', self.on_drop)
        self.listbox.dnd_bind('<<DragEnter>>', self.on_drag_enter)
        self.listbox.dnd_bind('<<DragLeave>>', self.on_drag_leave)

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

        tk.Button(bottom, text="Remove Selected (supports multi-select)",
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
        self.multi_selected_items.clear()
        self.last_clicked = None
        self.update_multi_select_label()

        if not self.root_dir:
            return

        # 创建根节点并设置为展开状态
        root_node = self.tree.insert(
            "",
            "end",
            text=os.path.basename(self.root_dir),
            values=[self.root_dir],
            open=True  # 设置为展开
        )

        # 【改进1】立即插入第一层子节点
        self.insert_children(root_node, self.root_dir)

    def insert_children(self, parent, path):
        # 清除占位符
        self.tree.delete(*self.tree.get_children(parent))

        entries = []
        try:
            for name in os.listdir(path):
                abs_path = os.path.join(path, name)
                if self.should_ignore(name):
                    continue
                if os.path.isdir(abs_path) or os.path.splitext(name)[1] in SUPPORTED_EXTS:
                    entries.append((name, abs_path))
        except PermissionError:
            return

        entries.sort(key=lambda x: (0 if os.path.isdir(x[1]) else 1, x[0].lower()))

        for name, abs_path in entries:
            node = self.tree.insert(parent, "end", text=name, values=[abs_path])
            if os.path.isdir(abs_path):
                self.tree.insert(node, "end")  # dummy

    def on_tree_expand(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        node = selection[0]

        # 检查是否有子节点
        children = self.tree.get_children(node)
        if children:
            # 检查第一个子节点是否是占位符（没有values）
            first_child = children[0]
            if not self.tree.item(first_child, "values"):
                # 是占位符，需要加载实际内容
                path = self.tree.item(node, "values")[0]
                if os.path.isdir(path):
                    self.insert_children(node, path)

    def on_tree_click(self, event):
        """【改进3】处理多选功能的单击事件"""
        # 获取点击的区域
        region = self.tree.identify_region(event.x, event.y)

        # 只处理在树项上的点击，忽略点击空白区域
        if region != "tree":
            return

        item = self.tree.identify_row(event.y)
        if not item:
            return

        # 检查节点是否有有效的 values
        values = self.tree.item(item, "values")
        if not values or len(values) == 0:
            return

        path = values[0]

        # 检查是否是文件
        if not os.path.isfile(path):
            # 文件夹不参与多选，但允许展开/折叠
            return

        # 检测修饰键
        ctrl_pressed = (event.state & 0x4) != 0  # Control key
        shift_pressed = (event.state & 0x1) != 0  # Shift key

        # 【修复】如果没有按修饰键，不阻止默认行为，让双击事件能触发
        if not ctrl_pressed and not shift_pressed:
            # 普通单击：清除之前的选择，只选中当前项
            self.multi_selected_items.clear()
            self.multi_selected_items.add(item)
            self.last_clicked = item
            self.tree.selection_set(list(self.multi_selected_items))
            self.update_multi_select_label()
            return  # 不返回 "break"，允许双击事件触发

        if ctrl_pressed:
            # Ctrl+点击：切换选择状态
            if item in self.multi_selected_items:
                self.multi_selected_items.remove(item)
            else:
                self.multi_selected_items.add(item)
            self.last_clicked = item
        elif shift_pressed and self.last_clicked:
            # Shift+点击：范围选择
            self.select_range(self.last_clicked, item)

        # 更新视觉选择
        self.tree.selection_set(list(self.multi_selected_items))

        # 更新多选状态标签
        self.update_multi_select_label()

        # 阻止默认的选择行为（仅在使用修饰键时）
        return "break"

    def select_range(self, start_item, end_item):
        """选择从start_item到end_item之间的所有文件"""
        # 获取所有可见的文件项
        all_files = self.get_all_file_items()

        try:
            start_idx = all_files.index(start_item)
            end_idx = all_files.index(end_item)

            # 确保start_idx <= end_idx
            if start_idx > end_idx:
                start_idx, end_idx = end_idx, start_idx

            # 选择范围内的所有项
            for i in range(start_idx, end_idx + 1):
                self.multi_selected_items.add(all_files[i])
        except ValueError:
            pass

    def update_multi_select_label(self):
        """更新多选状态标签"""
        count = len(self.multi_selected_items)
        if count == 0:
            self.multi_select_label.config(text="")
        elif count == 1:
            self.multi_select_label.config(text="(1 file selected)")
        else:
            self.multi_select_label.config(text=f"({count} files selected)")

    def get_all_file_items(self, parent=""):
        """递归获取所有文件节点（不包括文件夹）"""
        result = []
        for item in self.tree.get_children(parent):
            values = self.tree.item(item, "values")
            if values and len(values) > 0:
                path = values[0]
                if os.path.isfile(path):
                    result.append(item)
                # 递归获取子节点
                result.extend(self.get_all_file_items(item))
        return result

    def add_multi_selected_to_list(self):
        """【改进3】将树中多选的文件添加到右侧列表"""
        if not self.multi_selected_items:
            messagebox.showinfo("Info", "Please select files first (Ctrl+Click or Shift+Click)")
            return

        # 先保存所有选中的项到列表，避免在遍历时修改集合
        items_to_add = list(self.multi_selected_items)

        added_count = 0
        for item in items_to_add:
            values = self.tree.item(item, "values")
            if values and len(values) > 0:
                path = values[0]
                if os.path.isfile(path) and path not in self.selected_files:
                    self.selected_files.append(path)
                    added_count += 1

        if added_count > 0:
            self.refresh_listbox()
            # 清除多选状态
            self.multi_selected_items.clear()
            self.tree.selection_set([])
            self.update_multi_select_label()
            messagebox.showinfo("Success", f"Added {added_count} file(s) to the list")
        else:
            messagebox.showinfo("Info", "All selected files are already in the list")

    def on_tree_double_click(self, event):
        """双击添加单个文件（保留原功能）"""
        node = self.tree.focus()
        if not node:
            return

        values = self.tree.item(node, "values")
        if not values or len(values) == 0:
            return

        path = values[0]
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
        if idx >= len(self.selected_files):
            return
        path = self.selected_files[idx]
        self.highlight_in_tree(path)

    def highlight_in_tree(self, target):
        for item in self.tree.get_children():
            if self._search_tree(item, target):
                break

    def _search_tree(self, node, target):
        # 检查节点是否有 values（占位符节点没有）
        values = self.tree.item(node, "values")
        if values and len(values) > 0:
            if values[0] == target:
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
        """【改进2】带滚动条的过滤设置窗口"""
        win = tk.Toplevel(self.root)
        win.title("Filter Settings")
        win.geometry("450x400")
        win.configure(bg="#f7f7f7")

        # 主容器
        main_container = tk.Frame(win, bg="#f7f7f7")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # ===== 上部：可滚动的规则列表 =====
        rules_label = tk.Label(main_container, text="Ignore Rules:",
                               bg="#f7f7f7", font=("Arial", 11, "bold"))
        rules_label.pack(anchor="w", pady=(0, 5))

        # 创建滚动框架
        scroll_frame = tk.Frame(main_container, bg="#f7f7f7", relief="sunken", bd=1)
        scroll_frame.pack(fill="both", expand=True)

        # Canvas + Scrollbar
        canvas = tk.Canvas(scroll_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮支持
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)
        win.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # 填充规则列表
        vars_map = {}
        for rule, enabled in sorted(self.ignore_rules.items()):
            rule_frame = tk.Frame(scrollable_frame, bg="white")
            rule_frame.pack(fill="x", padx=5, pady=2)

            var = tk.BooleanVar(value=enabled)
            vars_map[rule] = var

            chk = tk.Checkbutton(
                rule_frame,
                text=rule,
                variable=var,
                bg="white",
                anchor="w",
                command=lambda r=rule, v=var: self.toggle_rule(r, v)
            )
            chk.pack(side="left", fill="x", expand=True)

            # 删除按钮（默认规则不显示）
            if rule not in DEFAULT_CONFIG["ignore_rules"]:
                del_btn = tk.Button(
                    rule_frame,
                    text="✕",
                    command=lambda r=rule, w=win: self.delete_rule(r, w),
                    bg="#f44336",
                    fg="white",
                    width=3,
                    relief="flat"
                )
                del_btn.pack(side="right", padx=2)

        # ===== 下部：添加新规则（固定位置）=====
        ttk.Separator(main_container, orient="horizontal").pack(fill="x", pady=10)

        add_frame = tk.Frame(main_container, bg="#f7f7f7")
        add_frame.pack(fill="x")

        tk.Label(add_frame, text="Add New Rule:", bg="#f7f7f7",
                 font=("Arial", 10)).pack(anchor="w", pady=(0, 3))

        entry_frame = tk.Frame(add_frame, bg="#f7f7f7")
        entry_frame.pack(fill="x")

        new_var = tk.StringVar()
        entry = tk.Entry(entry_frame, textvariable=new_var, font=("Arial", 10))
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        def add_rule():
            rule = new_var.get().strip()
            if not rule:
                messagebox.showwarning("Warning", "Please enter a rule pattern")
                return
            if rule in self.ignore_rules:
                messagebox.showinfo("Info", "Rule already exists")
                return

            self.ignore_rules[rule] = True
            self.save_config()
            messagebox.showinfo("Success", f"Rule '{rule}' added")
            win.destroy()
            if self.root_dir:
                self.populate_tree()

        tk.Button(entry_frame, text="Add Rule", command=add_rule,
                  bg="#4CAF50", fg="white", width=10).pack(side="right")

        # 提示信息
        hint = tk.Label(add_frame,
                        text="Tip: Use wildcards like *.log, test_*, etc.",
                        bg="#f7f7f7", font=("Arial", 8), fg="#666")
        hint.pack(anchor="w", pady=(3, 0))

    def toggle_rule(self, rule, var):
        self.ignore_rules[rule] = var.get()
        self.save_config()
        if self.root_dir:
            self.populate_tree()

    def delete_rule(self, rule, window):
        """删除自定义规则"""
        if messagebox.askyesno("Confirm", f"Delete rule '{rule}'?"):
            del self.ignore_rules[rule]
            self.save_config()
            window.destroy()
            if self.root_dir:
                self.populate_tree()
            # 重新打开设置窗口以显示更新
            self.open_filter_settings()

    # ================= 拖拽功能 =================
    def on_tree_button_press(self, event):
        """记录拖拽起始位置"""
        self.drag_start_index = self.tree.identify_row(event.y)

    def on_tree_motion(self, event):
        """处理拖拽移动 - 如果拖到右侧列表框，则添加文件"""
        if not self.drag_start_index:
            return

        # 检查鼠标是否移动到了列表框上方
        # 获取列表框的位置
        try:
            list_x = self.listbox.winfo_rootx()
            list_y = self.listbox.winfo_rooty()
            list_w = self.listbox.winfo_width()
            list_h = self.listbox.winfo_height()

            mouse_x = event.x_root
            mouse_y = event.y_root

            # 检查鼠标是否在列表框范围内
            if (list_x <= mouse_x <= list_x + list_w and
                    list_y <= mouse_y <= list_y + list_h):

                # 显示视觉反馈
                self.listbox.config(bg="#E3F2FD")

                # 绑定鼠标释放事件
                self.tree.bind("<ButtonRelease-1>", self.on_tree_drag_drop)
            else:
                self.listbox.config(bg="white")
        except:
            pass

    def on_tree_drag_drop(self, event):
        """拖拽释放 - 添加选中的文件到列表"""
        # 解绑事件
        self.tree.unbind("<ButtonRelease-1>")

        # 恢复背景
        self.listbox.config(bg="white")

        # 获取选中的项
        selected = self.tree.selection()
        if not selected:
            self.drag_start_index = None
            return

        # 收集文件
        added_count = 0
        for item in selected:
            values = self.tree.item(item, "values")
            if values and len(values) > 0:
                path = values[0]
                if os.path.isfile(path) and path not in self.selected_files:
                    self.selected_files.append(path)
                    added_count += 1

        # 刷新显示
        if added_count > 0:
            self.refresh_listbox()
            # 清除选中状态
            self.multi_selected_items.clear()
            self.tree.selection_set([])
            self.update_multi_select_label()
            messagebox.showinfo("Success", f"Added {added_count} file(s) via drag & drop")

        self.drag_start_index = None

    def on_drag_start(self, event):
        """开始拖拽时的处理（已弃用，保留以防需要）"""
        pass

    def on_drag_end(self, event):
        """拖拽结束时的处理（已弃用，保留以防需要）"""
        pass

    def on_drag_enter(self, event):
        """鼠标拖拽进入列表框时的视觉反馈"""
        self.listbox.config(bg="#E3F2FD")  # 浅蓝色背景
        return event.action

    def on_drag_leave(self, event):
        """鼠标拖拽离开列表框时恢复样式"""
        self.listbox.config(bg="white")

    def on_drop(self, event):
        """处理从系统拖入文件的事件"""
        self.listbox.config(bg="white")  # 恢复背景色

        # 解析拖放的数据
        data = event.data
        added_count = 0

        print(f"[DEBUG] Drop event data type: {type(data)}")
        print(f"[DEBUG] Drop event data: {repr(data)[:200]}")

        # 处理从系统文件管理器拖入的文件
        files = []

        if isinstance(data, str):
            # Windows 系统的文件路径可能用 {} 包裹
            if data.startswith('{'):
                # 处理多个文件的情况
                import re
                files = re.findall(r'\{([^}]+)\}', data)
                if not files:
                    files = [data.strip('{}')]
            else:
                # 可能是换行分隔
                if '\n' in data:
                    files = [f.strip() for f in data.split('\n') if f.strip()]
                else:
                    files = [data.strip()]

        print(f"[DEBUG] Parsed {len(files)} file(s)")

        for file_path in files:
            if not file_path:
                continue

            # 处理不同操作系统的路径格式
            # 移除 file:// 前缀
            original_path = file_path
            if file_path.startswith('file:///'):
                file_path = file_path[8:]
            elif file_path.startswith('file://'):
                file_path = file_path[7:]

            # Windows 路径可能有引号
            file_path = file_path.strip('"').strip("'")

            print(f"[DEBUG] Original: {original_path}")
            print(f"[DEBUG] Processed: {file_path}")
            print(f"[DEBUG] Exists: {os.path.isfile(file_path)}")

            # 检查文件是否存在
            if os.path.isfile(file_path):
                ext = os.path.splitext(file_path)[1]
                print(f"[DEBUG] Extension: {ext}, Supported: {ext in SUPPORTED_EXTS}")

                if ext in SUPPORTED_EXTS:
                    if file_path not in self.selected_files:
                        self.selected_files.append(file_path)
                        added_count += 1
                        print(f"[DEBUG] Added: {file_path}")
                    else:
                        print(f"[DEBUG] Already exists: {file_path}")
                else:
                    print(f"[DEBUG] Not supported type: {ext}")
            else:
                print(f"[DEBUG] File not found: {file_path}")

        print(f"[DEBUG] Total added: {added_count}")
        print(f"[DEBUG] Total selected files: {len(self.selected_files)}")

        if added_count > 0:
            self.refresh_listbox()
            messagebox.showinfo("Success", f"Added {added_count} file(s) from system")
        else:
            messagebox.showinfo("Info", "No supported files to add (check console for debug info)")

        return event.action


# =================== Run ===================
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    MergeToolTreeApp(root)
    root.mainloop()