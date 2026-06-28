# PyBuilder 🐍⚡

**Python一键打包工具** — 基于 PyInstaller，GUI + CLI 双模式，支持所有 PyInstaller 参数。

## 特点

- ✅ **双模式运行**：双击 GUI 界面操作 / 命令行集成
- ✅ **完整参数支持**：基本设置、输出、界面、数据导入、高级选项、压缩、平台
- ✅ **独立控制台窗口**：打包时弹出黑窗口显示完整 PyInstaller 日志，完成后 3 秒自动关闭
- ✅ **配置保存/加载**：保存打包配置，下次一键加载
- ✅ **自动查找 Python**：已打包成 exe 后自动搜索系统上的 Python 解释器
- ✅ **轻量简洁**：单文件 Python 脚本，Tkinter 原生界面

## 快速开始

### 方式一：直接运行 exe（推荐）

项目根目录的 `PyBuilder.exe` 双击运行即可。首次启动会自动在桌面创建快捷方式。

### 方式二：Python 源码运行

```bash
python pybuilder.py
```

### 安装依赖

如果提示 `PyInstaller` 不可用，双击 `安装依赖.bat` 自动安装。

## 使用截图

| 界面 Tab | 功能 |
|----------|------|
| 基本设置 | 选择脚本、程序名称、单文件/目录模式 |
| 输出设置 | 输出目录、工作目录、清理缓存 |
| 界面设置 | 无控制台模式、程序图标 |
| 数据/导入 | 附加数据、附加二进制、隐藏/排除模块 |
| 高级选项 | 版本信息、日志级别、加密密钥、调试模式 |
| 收集/压缩 | 收集全部、复制元数据、压缩级别、UPX 目录 |
| 平台选项 | 管理员权限、目标架构 |

## 命令行模式

```bash
# 打包成单文件
python pybuilder.py my_script.py --onefile -n MyApp

# 打包成目录
python pybuilder.py my_script.py --onedir --windowed

# 指定图标和输出目录
python pybuilder.py my_script.py --onefile -i icon.ico -d ./output
```

## 版本说明

每次发布新版本时，源码和 exe 都会带上版本号：

```
PyBuilder_V1.0/              # V1.0 发布目录
├── pybuilder_V1.0.py         # 带版本号的源码
├── PyBuilder_V1.0.exe        # 带版本号的 exe
├── app_icon.ico
└── README.md

PyBuilder_V2.0/              # V2.0 发布目录
├── pybuilder_V2.0.py
├── PyBuilder_V2.0.exe
├── app_icon.ico
└── README.md
```

## 项目结构

```
PyBuilder/
├── pybuilder.py             # 主程序源码（版本号在内部）
├── pybuilder_V1.0.py        # 带版本号的源码副本
├── PyBuilder_V1.0.exe       # 打包好的可执行文件
├── setup_shortcut.py        # 桌面快捷方式创建脚本
├── app_icon.ico             # 程序图标
├── app_icon.png             # 图标 PNG
├── 安装依赖.bat             # 依赖安装脚本
├── .gitignore
├── dist/                    # 打包输出目录
└── README.md
```

## 技术说明

- GUI 基于 Python Tkinter（原生，零依赖）
- 打包引擎：PyInstaller（需单独安装）
- exe 打包使用 PyInstaller --onefile --windowed
