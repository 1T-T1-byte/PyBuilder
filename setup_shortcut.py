"""创建 PyBuilder 桌面快捷方式（双击运行此文件即可）"""
import os, sys
import win32com.client

project_dir = os.path.dirname(os.path.abspath(__file__))
target_exe = os.path.join(project_dir, 'PyBuilder.exe')

if not os.path.exists(target_exe):
    print(f"错误: 找不到 {target_exe}")
    sys.exit(1)

desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
shortcut_path = os.path.join(desktop, 'PyBuilder.lnk')

shell = win32com.client.Dispatch('WScript.Shell')
sc = shell.CreateShortcut(shortcut_path)
sc.TargetPath = target_exe
sc.WorkingDirectory = project_dir
sc.Description = 'PyBuilder - Python打包工具'
sc.Save()

print(f"✅ 快捷方式已创建: {shortcut_path}")
print(f"📁 目标: {target_exe}")
print(f"📁 工作目录: {project_dir}")
