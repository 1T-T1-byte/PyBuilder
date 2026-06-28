#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyBuilder - Python打包工具（单文件版）
支持GUI和命令行，支持PyInstaller所有常用参数
"""
import os
import sys
import argparse
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json


# ======================== 配置 ========================

PARAM_GROUPS = [
    ("基本设置", [
        ("script",          "脚本文件",       "file",   None,  True,  "要打包的Python脚本"),
        ("--name",          "程序名称",        "str",   "-n",  False, "打包后的可执行文件名"),
        ("--onefile",       "单文件模式(-F)",  "bool",  "-F",  False, "打包成单个exe文件"),
        ("--onedir",        "目录模式(-D)",   "bool",  "-D",  False, "打包成一个文件夹"),
    ]),
    ("输出设置", [
        ("--distpath",      "输出目录",        "dir",   "-d",  False, "输出目录（默认./dist）"),
        ("--workpath",      "工作目录",        "dir",   "-w",  False, "工作目录（默认./build）"),
        ("--clean",         "清理缓存(-y)",   "bool",  "-y",  False, "打包前清理build/dist目录"),
    ]),
    ("界面设置", [
        ("--windowed",     "无控制台",       "bool",  "-w",  False, "GUI程序，不显示控制台窗口"),
        ("--icon",          "程序图标",        "file",  "-i",  False, "图标文件（.ico/.png）"),
    ]),
    ("数据/导入", [
        ("--add-data",     "附加数据",        "str",   "",    False, "格式: src;dest（多个用逗号分隔）"),
        ("--add-binary",   "附加二进制",      "str",   "",    False, "格式: src;dest"),
        ("--hidden-import","隐藏导入",        "str",   "",    False, "隐藏导入模块（多个用逗号分隔）"),
        ("--exclude-module","排除模块",        "str",   "",    False, "排除模块（多个用逗号分隔）"),
    ]),
    ("高级选项", [
        ("--version-file",  "版本信息文件",   "file",  "",    False, "Windows版本信息文件"),
        ("--runtime-hook", "运行时钩子",     "file",  "",    False, "运行时钩子脚本"),
        ("--log-level",    "日志级别",        "choice","",    False, "日志级别","TRACE|DEBUG|INFO|WARN|ERROR|CRITICAL"),
        ("--key",           "加密密钥",        "str",   "-k",  False, "PyInstaller字节码加密密钥"),
        ("--debug",         "调试模式",        "bool",  "",    False, "启用调试模式"),
    ]),
    ("收集/压缩", [
        ("--collect-all",  "收集全部",       "str",   "",    False, "收集指定包的所有数据（多个用逗号分隔）"),
        ("--copy-metadata","复制元数据",      "str",   "",    False, "复制包的元数据（多个用逗号分隔）"),
        ("--compress",     "压缩级别",        "choice","",    False, "压缩级别(0-9)","0|1|2|3|4|5|6|7|8|9"),
        ("--upx-dir",      "UPX目录",        "dir",   "",    False, "UPX压缩工具目录"),
    ]),
    ("平台选项", [
        ("--uac-admin",    "管理员权限",      "bool",  "",    False, "请求管理员权限(Windows)"),
        ("--target-arch",  "目标架构",        "choice","",    False, "macOS目标架构","x86_64|arm64|universal2"),
        ("--entitlements", "权限文件",        "file",  "",    False, "macOS entitlements文件"),
    ]),
]


# ======================== 核心 ========================

class Builder:
    def __init__(self):
        self.callback = None
        self._python_exe = None

    def set_callback(self, cb):
        self.callback = cb

    def log(self, msg, level="INFO"):
        if self.callback:
            self.callback(msg, level)
        else:
            print(f"[{level}] {msg}")

    def find_python(self):
        """查找系统上可用的Python解释器"""
        # 1. 未打包模式：sys.executable 就是 python.exe
        if not getattr(sys, 'frozen', False):
            return sys.executable

        # 2. 已打包模式：搜索系统python
        import shutil

        # 2a. PATH 中的 python
        for name in ["python", "python3", "py"]:
            exe = shutil.which(name)
            if exe:
                return exe

        # 2b. 常见安装路径
        for ver in range(13, 8, -1):
            path = rf"C:\Python{ver}\python.exe"
            if os.path.exists(path):
                return path

        # 2c. Program Files
        for ver in ["13", "12", "11", "10", "39", "38"]:
            for base in [os.environ.get("ProgramFiles", "C:\\Program Files"),
                         os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")]:
                path = os.path.join(base, f"Python{ver}", "python.exe")
                if os.path.exists(path):
                    return path
                path = os.path.join(base, f"Python", f"Python{ver}", "python.exe")
                if os.path.exists(path):
                    return path

        # 2d. 环境变量 PythonPath 或注册表（Windows）
        try:
            import winreg
            for ver in ["3.13", "3.12", "3.11", "3.10", "3.9"]:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                        rf"SOFTWARE\Python\PythonCore\{ver}\InstallPath")
                    path = winreg.QueryValue(key, "")
                    winreg.CloseKey(key)
                    if path and os.path.exists(path):
                        exe = os.path.join(path, "python.exe")
                        if os.path.exists(exe):
                            return exe
                except:
                    pass
        except:
            pass

        return None

    def build_cmd(self, args):
        cmd = ["pyinstaller"]
        for key, val in vars(args).items():
            if key == "script":
                if val:
                    cmd.append(val)
                continue
            if val is None:
                continue
            # 查找参数配置（兼容带 -- 和不带 -- 的 key）
            ptype, parg = "str", key
            for group in PARAM_GROUPS:
                for p in group[1]:
                    pkey = p[0].lstrip("-")  # 去掉 -- 前缀
                    if p[0] == key or pkey == key:
                        ptype, parg = p[2], p[3]
                        break
            arg = parg if parg else ("--" + key if not key.startswith("-") else key)
            if ptype == "bool":
                if val:
                    cmd.append(arg)
            elif isinstance(val, list):
                for v in val:
                    cmd.extend([arg, v])
            elif val:
                cmd.extend([arg, str(val)])
        return cmd

    def run(self, args):
        try:
            # 1. 查找Python解释器
            python_exe = self.find_python()
            if not python_exe:
                self.log("未找到Python解释器！请确保已安装Python并添加到PATH", "ERROR")
                return False

            self.log(f"使用Python: {python_exe}", "INFO")

            # 2. 检查PyInstaller是否可用（静默检查，不弹窗）
            check_result = subprocess.run(
                [python_exe, "-m", "PyInstaller", "--version"],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if check_result.returncode != 0:
                stderr = check_result.stderr.strip()
                self.log(f"PyInstaller不可用！请先安装：python -m pip install pyinstaller", "ERROR")
                if stderr:
                    self.log(f"详情: {stderr[:200]}", "ERROR")
                return False

            py_ver = check_result.stdout.strip()
            self.log(f"PyInstaller版本: {py_ver}", "INFO")

            # 3. 强制输出到 dist 目录
            if not getattr(args, "distpath", None):
                args.distpath = os.path.join(os.getcwd(), "dist")

            # 4. 构建命令
            cmd = self.build_cmd(args)
            py_cmd = [python_exe, "-m", "PyInstaller"] + cmd[1:]
            cmd_line = subprocess.list2cmdline(py_cmd)

            self.log("=" * 60, "INFO")
            self.log("执行命令:", "INFO")
            self.log(cmd_line, "INFO")
            self.log("=" * 60, "INFO")
            self.log("已弹出独立控制台窗口，详细日志请查看黑窗口", "INFO")
            self.log("-" * 60, "INFO")

            # 5. 创建临时批处理文件
            #    在新控制台窗口中运行PyInstaller，完成后等待3秒自动关闭
            bat_dir = os.path.join(os.getcwd(), "dist")
            os.makedirs(bat_dir, exist_ok=True)
            bat_path = os.path.join(bat_dir, "_pybuilder_run.bat")
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write("@echo off\n")
                f.write("chcp 65001 >nul 2>&1\n")
                f.write(f'cd /d "{os.getcwd()}"\n')
                f.write("echo.\n")
                f.write(f"{cmd_line}\n")
                f.write("echo.\n")
                f.write("if %errorlevel%==0 (\n")
                f.write("  echo [SUCCESS] ============================================\n")
                f.write("  echo [SUCCESS] 打包成功！\n")
                f.write(f'  echo [SUCCESS] 输出目录: {args.distpath}\n')
                f.write("  echo [SUCCESS] ============================================\n")
                f.write(") else (\n")
                f.write("  echo [ERROR] ============================================\n")
                f.write("  echo [ERROR] 打包失败！请检查上面的错误信息\n")
                f.write("  echo [ERROR] ============================================\n")
                f.write(")\n")
                f.write("echo.\n")
                f.write("echo 窗口将在 3 秒后自动关闭...\n")
                f.write("timeout /t 3 /nobreak >nul\n")

            # 6. 在新控制台窗口中执行
            proc = subprocess.Popen(
                ["cmd.exe", "/c", bat_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            proc.wait()  # 等控制台窗口关闭

            # 7. 清理临时bat
            try:
                if os.path.exists(bat_path):
                    os.unlink(bat_path)
            except:
                pass

            self.log("-" * 60, "INFO")
            if proc.returncode == 0:
                self.log("打包成功!", "INFO")
                self.log(f"输出目录: {args.distpath}", "INFO")
            else:
                self.log("打包失败! 请查看弹出的黑窗口中的错误信息", "ERROR")
            self.log("=" * 60, "INFO")
            return True
        except subprocess.TimeoutExpired:
            self.log("PyInstaller检测超时", "ERROR")
            return False
        except Exception as e:
            self.log(f"错误: {e}", "ERROR")
            import traceback
            tb = traceback.format_exc()
            self.log(tb, "ERROR")
            return False


# ======================== GUI ========================

class GUI:
    def __init__(self):
        # 高DPI支持
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        self.root = tk.Tk()
        self.root.title("PyBuilder")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        self.builder = Builder()
        self.builder.set_callback(self.log)

        self.entries = {}
        self.checks = {}
        self.combos = {}

        self._build_ui()

    def _build_ui(self):
        root = self.root

        # 标题
        hdr = ttk.Frame(root)
        hdr.pack(fill="x", padx=10, pady=(10, 5))
        ttk.Label(hdr, text="PyBuilder", font=("Microsoft YaHei", 16, "bold")).pack(side="left")
        ttk.Label(hdr, text="Python打包工具 | 支持PyInstaller所有参数",
                  font=("Microsoft YaHei", 9), foreground="gray").pack(side="left", padx=(8, 0))

        # 中间区域
        mid = ttk.Frame(root)
        mid.pack(fill="both", expand=True, padx=10, pady=5)

        # 左侧：Notebook参数分页
        nb = ttk.Notebook(mid)
        nb.pack(side="left", fill="both", expand=True)
        for grp_name, grp_params in PARAM_GROUPS:
            tab = ttk.Frame(nb, padding=10)
            nb.add(tab, text=grp_name)
            self._build_tab(tab, grp_params)

        # 右侧：日志
        log_frame = ttk.Frame(mid, width=320)
        log_frame.pack(side="right", fill="both", padx=(10, 0))
        log_frame.pack_propagate(False)

        ttk.Label(log_frame, text="打包日志", font=("Microsoft YaHei", 11, "bold")).pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(
            log_frame, font=("Consolas", 10),
            bg="#1e1e1e", fg="#00ff00", insertbackground="white"
        )
        self.log_text.pack(fill="both", expand=True, pady=(5, 0))

        # 底部按钮
        btns = ttk.Frame(root)
        btns.pack(fill="x", padx=10, pady=8)

        ttk.Button(btns, text="选择脚本", command=self._select_script).pack(side="left", padx=4)
        ttk.Button(btns, text="加载配置", command=self._load_cfg).pack(side="left", padx=4)
        ttk.Button(btns, text="保存配置", command=self._save_cfg).pack(side="left", padx=4)
        ttk.Button(btns, text="重置", command=self._reset).pack(side="left", padx=4)
        self.start_btn = ttk.Button(btns, text="开始打包", command=self._start_build)
        self.start_btn.pack(side="right", padx=4)

    def _build_tab(self, parent, params):
        row = col = 0
        for key, name, ptype, _, _, help_text, *extra in params:
            if ptype == "bool":
                var = tk.BooleanVar()
                self.checks[key] = var

                # 单文件/目录模式互斥
                if key in ("--onefile", "--onedir"):
                    def make_mode_cmd(k, v):
                        return lambda: self._toggle_mode(k, v)
                    cb = ttk.Checkbutton(parent, text=name, variable=var, command=make_mode_cmd(key, var))
                    cb.grid(row=row, column=col, columnspan=3, sticky="w", padx=5, pady=4)
                else:
                    ttk.Checkbutton(parent, text=name, variable=var).grid(
                        row=row, column=col, columnspan=3, sticky="w", padx=5, pady=4)
                col += 3
                if col >= 6:
                    col, row = 0, row + 1
            elif ptype in ("file", "dir"):
                ttk.Label(parent, text=f"{name}:").grid(row=row, column=col, sticky="e", padx=(5, 2), pady=4)
                col += 1
                ent = ttk.Entry(parent, width=28)
                ent.grid(row=row, column=col, sticky="ew", padx=2, pady=4)
                self.entries[key] = ent
                col += 1
                ttk.Button(parent, text="浏览" if ptype == "file" else "选择", width=6,
                          command=lambda k=key, t=ptype: self._browse(k, t)
                          ).grid(row=row, column=col, padx=(2, 5), pady=4)
                col += 1
                if col >= 6:
                    col, row = 0, row + 1
            elif ptype == "choice":
                ttk.Label(parent, text=f"{name}:").grid(row=row, column=col, sticky="e", padx=(5, 2), pady=4)
                col += 1
                combo = ttk.Combobox(parent, values=extra[0].split("|"), width=18, state="readonly")
                combo.grid(row=row, column=col, sticky="w", padx=2, pady=4)
                self.combos[key] = combo
                col += 1
                if col >= 6:
                    col, row = 0, row + 1
            elif ptype == "str":
                ttk.Label(parent, text=f"{name}:").grid(row=row, column=col, sticky="e", padx=(5, 2), pady=4)
                col += 1
                ent = ttk.Entry(parent, width=28)
                ent.grid(row=row, column=col, sticky="ew", padx=2, pady=4)
                self.entries[key] = ent
                col += 1
                if help_text and col < 6:
                    ttk.Label(parent, text=help_text, font=("", 8), foreground="gray"
                             ).grid(row=row, column=col, sticky="w", padx=(2, 5))
                    col += 1
                if col >= 6:
                    col, row = 0, row + 1

        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(3, weight=1)
        parent.columnconfigure(5, weight=1)

    def _toggle_mode(self, selected_key, selected_var):
        """互斥选项处理"""
        if selected_var.get():
            # 打包模式互斥
            if selected_key in ("--onefile", "--onedir"):
                other = "--onedir" if selected_key == "--onefile" else "--onefile"
                other_var = self.checks.get(other)
                if other_var:
                    other_var.set(False)
            # 窗口模式互斥
            elif selected_key in ("--windowed", "--noconsole"):
                other = "--noconsole" if selected_key == "--windowed" else "--windowed"
                other_var = self.checks.get(other)
                if other_var:
                    other_var.set(False)

    def _browse(self, key, ftype):
        path = filedialog.askopenfilename(title=f"选择{key}") if ftype == "file" \
            else filedialog.askdirectory(title=f"选择{key}目录")
        if path:
            ent = self.entries.get(key)
            if ent:
                ent.delete(0, "end")
                ent.insert(0, path)

    def _select_script(self):
        path = filedialog.askopenfilename(title="选择Python脚本",
                                         filetypes=[("Python", "*.py"), ("All", "*.*")])
        if path:
            ent = self.entries.get("script")
            if ent:
                ent.delete(0, "end")
                ent.insert(0, path)
            self.log(f"已选择: {path}", "INFO")

    def _get_args(self):
        args = argparse.Namespace()
        list_keys = {"--hidden-import", "--exclude-module", "--collect-all", "--copy-metadata"}
        for k, ent in self.entries.items():
            val = ent.get().strip()
            key = k.lstrip("-")  # 统一去掉 -- 前缀
            if key == "script":
                args.script = val or None
            elif not val:
                setattr(args, key, None)
            elif k in list_keys:
                setattr(args, key, [v.strip() for v in val.split(",") if v.strip()])
            else:
                setattr(args, key, val)
        for k, v in self.checks.items():
            setattr(args, k.lstrip("-"), v.get())
        for k, combo in self.combos.items():
            val = combo.get()
            setattr(args, k.lstrip("-"), val if val else None)
        return args

    def _start_build(self):
        args = self._get_args()
        if not getattr(args, "script", None):
            messagebox.showwarning("警告", "请先选择要打包的Python脚本！")
            return
        if not os.path.exists(args.script):
            messagebox.showerror("错误", f"脚本不存在:\n{args.script}")
            return

        # 禁用按钮，防止重复点击
        self.start_btn.config(state="disabled", text="打包中...")
        self.log_text.delete("1.0", "end")
        self.log("=" * 50, "INFO")
        self.log("开始打包，请稍候...", "INFO")
        self.log("=" * 50, "INFO")

        def run_build():
            try:
                self.builder.run(args)
            finally:
                # 无论成功还是失败，都要恢复按钮
                self.root.after(0, lambda: self.start_btn.config(state="normal", text="开始打包"))

        threading.Thread(target=run_build, daemon=True).start()

    def _load_cfg(self):
        path = filedialog.askopenfilename(title="加载配置", filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in cfg.items():
                if k in self.checks:
                    self.checks[k].set(v)
                elif k in self.entries:
                    self.entries[k].delete(0, "end")
                    self.entries[k].insert(0, str(v))
                elif k in self.combos:
                    self.combos[k].set(str(v))
            self.log(f"已加载: {path}", "INFO")
            messagebox.showinfo("成功", "配置加载成功！")
        except Exception as e:
            messagebox.showerror("错误", f"加载失败:\n{e}")

    def _save_cfg(self):
        path = filedialog.asksaveasfilename(title="保存配置", defaultextension=".json",
                                            filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if not path:
            return
        try:
            cfg = {}
            for k, v in self.checks.items():
                cfg[k] = v.get()
            for k, ent in self.entries.items():
                val = ent.get().strip()
                if val:
                    cfg[k] = val
            for k, combo in self.combos.items():
                val = combo.get()
                if val:
                    cfg[k] = val
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            self.log(f"已保存: {path}", "INFO")
            messagebox.showinfo("成功", "配置保存成功！")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败:\n{e}")

    def _reset(self):
        for v in self.checks.values():
            v.set(False)
        for ent in self.entries.values():
            ent.delete(0, "end")
        for combo in self.combos.values():
            combo.set("")
        self.log_text.delete("1.0", "end")
        self.log("已重置", "INFO")

    def log(self, msg, level="INFO"):
        self.log_text.insert("end", f"[{level}] {msg}\n")
        self.log_text.see("end")

    def run(self):
        self.root.mainloop()


# ======================== 入口 ========================

def main():
    # 找到项目根目录并切换工作目录
    if getattr(sys, 'frozen', False):
        project_root = os.path.dirname(os.path.abspath(sys.executable))
    else:
        project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root:
        os.chdir(project_root)

    # 自动创建桌面快捷方式（仅在打包成exe时）
    if getattr(sys, 'frozen', False):
        try:
            import win32com.client
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            lnk_path = os.path.join(desktop, 'PyBuilder.lnk')
            if not os.path.exists(lnk_path):
                shell = win32com.client.Dispatch('WScript.Shell')
                sc = shell.CreateShortcut(lnk_path)
                sc.TargetPath = sys.executable
                sc.WorkingDirectory = project_root
                sc.Description = 'PyBuilder - Python打包工具'
                sc.Save()
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="PyBuilder - Python打包工具",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="示例:\n  GUI模式:     python pybuilder.py\n  命令行模式:   python pybuilder.py myscript.py --onefile\n  附加数据(Win): python pybuilder.py -c a.py --add-data \"res;res\"")
    parser.add_argument("script", nargs="?", help="脚本文件")
    parser.add_argument("--name", "-n", help="程序名称")
    parser.add_argument("--onefile", "-F", action="store_true", help="单文件模式")
    parser.add_argument("--onedir", "-D", action="store_true", help="目录模式")
    parser.add_argument("--windowed", "-w", action="store_true", help="窗口模式")
    parser.add_argument("--noconsole", action="store_true", help="无控制台")
    parser.add_argument("--icon", "-i", help="程序图标")
    parser.add_argument("--distpath", "-d", help="输出目录")
    parser.add_argument("--workpath", help="工作目录")
    parser.add_argument("--clean", "-y", action="store_true", help="清理缓存")
    parser.add_argument("--add-data", action="append", help="附加数据")
    parser.add_argument("--add-binary", action="append", help="附加二进制")
    parser.add_argument("--hidden-import", action="append", help="隐藏导入")
    parser.add_argument("--exclude-module", action="append", help="排除模块")
    parser.add_argument("--collect-all", action="append", help="收集全部")
    parser.add_argument("--copy-metadata", action="append", help="复制元数据")
    parser.add_argument("--compress", help="压缩级别")
    parser.add_argument("--upx-dir", help="UPX目录")
    parser.add_argument("--log-level", choices=["TRACE","DEBUG","INFO","WARN","ERROR","CRITICAL"], default="INFO")
    parser.add_argument("--key", "-k", help="加密密钥")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--version-file", help="版本信息文件")
    parser.add_argument("--runtime-hook", help="运行时钩子")
    parser.add_argument("--uac-admin", action="store_true", help="管理员权限")
    parser.add_argument("--save-config", metavar="FILE", help="保存配置")
    parser.add_argument("--load-config", metavar="FILE", help="加载配置")

    args = parser.parse_args()

    if args.load_config:
        with open(args.load_config, encoding="utf-8") as f:
            cfg = json.load(f)
        for k, v in cfg.items():
            setattr(args, k, v)
        args.load_config = None

    if args.save_config:
        cfg = {k: v for k, v in vars(args).items() if v is not None and k not in ("save_config", "load_config")}
        with open(args.save_config, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        print(f"配置已保存: {args.save_config}")
        return

    # 无脚本参数时启动GUI
    if not args.script and not args.load_config:
        GUI().run()
    else:
        b = Builder()
        b.set_callback(lambda msg, lv: print(f"[{lv}] {msg}"))
        b.run(args)


if __name__ == "__main__":
    main()
