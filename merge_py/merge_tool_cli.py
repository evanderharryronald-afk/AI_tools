import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# =================== Helper Functions ===================
def get_all_py_files(paths):
    """Recursively get all Python files from given paths."""
    py_files = []
    for path in paths:
        if os.path.isfile(path) and path.endswith(".py"):
            py_files.append(os.path.abspath(path))
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".py"):
                        py_files.append(os.path.join(root, file))
    return py_files

def merge_files_with_relative_paths(files, root_dir):
    """Merge files with paths relative to root_dir, using '/' as separator."""
    merged_code = []
    for file in files:
        relative_path = os.path.relpath(file, root_dir).replace("\\", "/")
        with open(file, "r", encoding="utf-8") as f:
            merged_code.append(f"# ===== File: {relative_path} =====\n")
            merged_code.append(f.read().strip() + "\n\n")
    return merged_code

def save_merged_code(merged_code):
    """Ask user where to save the merged file."""
    save_path = filedialog.asksaveasfilename(
        title="Save merged Python file",
        defaultextension=".py",
        initialfile="merged_code.py",
        filetypes=[("Python Files", "*.py")]
    )
    if save_path:
        with open(save_path, "w", encoding="utf-8") as f:
            f.writelines(merged_code)
        messagebox.showinfo("Done", f"Merged file saved:\n{save_path}")
    else:
        messagebox.showinfo("Info", "File not saved")

# =================== GUI Application ===================
class MergeToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Merge Tool")
        self.root.geometry("750x500")
        self.root.configure(bg="#f7f7f7")

        self.root_dir = None
        self.selected_files = []

        # --- Top Frame: Root Directory ---
        top_frame = tk.Frame(root, bg="#f7f7f7")
        top_frame.pack(fill="x", padx=10, pady=10)

        self.root_label = tk.Label(top_frame, text="Root Directory: Not selected", bg="#f7f7f7", font=("Arial", 12), anchor="w")
        self.root_label.pack(side="left", fill="x", expand=True)

        select_root_btn = tk.Button(top_frame, text="Select Root Directory", command=self.select_root_directory, bg="#2196F3", fg="white", padx=10, pady=5)
        select_root_btn.pack(side="right", padx=5)

        # --- Middle Frame: File List ---
        middle_frame = tk.Frame(root, bg="#f7f7f7")
        middle_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.file_listbox = tk.Listbox(middle_frame, selectmode=tk.MULTIPLE, font=("Consolas", 11))
        self.file_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(middle_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        # --- File Count Label ---
        self.count_label = tk.Label(root, text="Selected files: 0", bg="#f7f7f7", font=("Arial", 11))
        self.count_label.pack(pady=(0,10))

        # --- Bottom Frame: Buttons ---
        bottom_frame = tk.Frame(root, bg="#f7f7f7")
        bottom_frame.pack(fill="x", padx=10, pady=10)

        add_files_btn = tk.Button(bottom_frame, text="Add Files/Folders", command=self.add_files, bg="#4CAF50", fg="white", padx=10, pady=5)
        add_files_btn.pack(side="left", padx=5)

        remove_selected_btn = tk.Button(bottom_frame, text="Remove Selected", command=self.remove_selected, bg="#FF9800", fg="white", padx=10, pady=5)
        remove_selected_btn.pack(side="left", padx=5)

        clear_btn = tk.Button(bottom_frame, text="Clear All", command=self.clear_all, bg="#f44336", fg="white", padx=10, pady=5)
        clear_btn.pack(side="left", padx=5)

        merge_btn = tk.Button(bottom_frame, text="Merge Now", command=self.merge_now, bg="#673AB7", fg="white", padx=10, pady=5)
        merge_btn.pack(side="right", padx=5)

    # --- GUI Callbacks ---
    def select_root_directory(self):
        dir_selected = filedialog.askdirectory(title="Select Project Root Directory")
        if dir_selected:
            self.root_dir = os.path.abspath(dir_selected)
            self.root_label.config(text=f"Root Directory: {self.root_dir}")

            # Update displayed relative paths if files already selected
            self.refresh_file_list_display()

    def add_files(self):
        if not self.root_dir:
            messagebox.showwarning("Warning", "Please select a root directory first.")
            return

        paths = filedialog.askopenfilenames(title="Select Python Files or Folders")
        if not paths:
            return

        py_files = get_all_py_files(paths)
        added_count = 0
        for f in py_files:
            if f not in self.selected_files:
                self.selected_files.append(f)
                added_count += 1

        self.refresh_file_list_display()
        messagebox.showinfo("Info", f"Added {added_count} Python files.")

    def remove_selected(self):
        selected_indices = list(self.file_listbox.curselection())
        for index in reversed(selected_indices):
            self.selected_files.pop(index)
        self.refresh_file_list_display()

    def clear_all(self):
        self.selected_files.clear()
        self.refresh_file_list_display()

    def merge_now(self):
        if not self.root_dir:
            messagebox.showwarning("Warning", "Please select a root directory first.")
            return
        if not self.selected_files:
            messagebox.showwarning("Warning", "No Python files selected for merging.")
            return

        merged_code = merge_files_with_relative_paths(self.selected_files, self.root_dir)
        save_merged_code(merged_code)

    def refresh_file_list_display(self):
        self.file_listbox.delete(0, tk.END)
        for f in self.selected_files:
            if self.root_dir:
                rel_path = os.path.relpath(f, self.root_dir).replace("\\", "/")
            else:
                rel_path = f
            self.file_listbox.insert(tk.END, rel_path)
        self.count_label.config(text=f"Selected files: {len(self.selected_files)}")

# =================== Run App ===================
if __name__ == "__main__":
    root = tk.Tk()
    app = MergeToolApp(root)
    root.mainloop()
