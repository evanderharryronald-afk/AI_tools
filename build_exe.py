import PyInstaller.__main__
import os
import tkinterdnd2
import shutil
import sys

# 1. Get the path of the dependency library
# 自动获取 tkinterdnd2 库的路径
dnd_path = os.path.dirname(tkinterdnd2.__file__)

# 2. Define path variables (Use absolute paths to avoid confusion)
# 使用绝对路径，防止 PyInstaller 在临时目录找不到文件
base_dir = os.path.abspath(os.path.dirname(__file__))
source_file = os.path.join(base_dir, "merge_py", "AI_ready_code_weaver_v2.py")
config_file = os.path.join(base_dir, "merge_py", "merge_tool_config.json")
output_dir = os.path.join(base_dir, "output")

# Create output directory if it doesn't exist
# 如果 output 文件夹不存在则创建
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print(f"🚀 Starting build process... Target directory: {output_dir}")

# 3. Execute PyInstaller
PyInstaller.__main__.run([
    source_file,
    '--name=CodeWeaver_v2',
    '--onefile',
    '--windowed',
    '--clean',
    # 修正点：这里必须加上 '--add-data' 前缀
    '--add-data', f'{config_file}{os.pathsep}.',
    # 打包 tkinterdnd2 依赖
    '--add-data', f'{dnd_path}{os.pathsep}tkinterdnd2',
    # 指定输出到 output 文件夹
    f'--distpath={output_dir}',
    '--workpath=build_temp',
    '--specpath=build_temp'
])



# 4. Cleanup temporary build files
# 清理不需要的临时构建文件
if os.path.exists("build_temp"):
    shutil.rmtree("build_temp")

print(f"\n✅ Build Successful! Locate your app at: {os.path.abspath(output_dir)}")