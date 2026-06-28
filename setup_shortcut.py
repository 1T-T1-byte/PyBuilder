"""创建 PyBuilder 桌面快捷方式（双击运行此文件即可）"""
import os, sys, glob
import win32com.client

project_dir = os.path.dirname(os.path.abspath(__file__))

# 自动查找最新版本的 PyBuilder_V*.exe
exe_list = glob.glob(os.path.join(project_dir, 'PyBuilder_V*.exe'))
if not exe_list:
    print(f"错误: 找不到 PyBuilder_V*.exe")
    sys.exit(1)
target_exe = max(exe_list, key=os.path.getmtime)  # 取最新的

desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
shortcut_path = os.path.join(desktop, 'PyBuilder.lnk')

shell = win32com.client.Dispatch('WScript.Shell')
sc = shell.CreateShortcut(shortcut_path)
sc.TargetPath = target_exe
sc.WorkingDirectory = project_dir
sc.Description = f'PyBuilder {os.path.splitext(os.path.basename(target_exe))[0]} - Python打包工具'
sc.Save()

print(f"✅ 快捷方式已更新: {shortcut_path}")
print(f"📁 目标: {target_exe}")
print(f"📁 工作目录: {project_dir}")
