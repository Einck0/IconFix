# IconFix 2.0

`IconFix` 用于修复 Windows 上 Steam 游戏快捷方式图标丢失、变白或失效的问题。程序会扫描 `.url` 快捷方式，提取其中的 `Steam App ID` 与图标文件路径，然后重新下载官方图标并写回本地。

## 2.0 版本改进

- 将单文件脚本重构为清晰的包结构，方便维护和扩展。
- 增加更稳健的管理员提权流程：
  非管理员启动时会主动申请管理员权限，用户允许后会自动以提权态继续执行。
- 补充命令行参数、版本号与项目元信息。
- 增加基础测试，便于后续继续迭代。
- 补充更完整的使用说明与优化学习笔记。

## 工作原理

1. 扫描指定目录和公共桌面中的 `.url` 快捷方式。
2. 解析快捷方式中的 `URL=steam://rungameid/...` 与 `IconFile=...`。
3. 从 Steam 静态资源地址重新下载 `.ico` 图标。
4. 将图标写回原快捷方式引用的本地图标文件。

## 环境要求

- Windows
- Python 3.10+
- v2.0 无第三方运行时依赖

## 安装方式

```powershell
pip install -r requirements.txt
```

`requirements.txt` 在 2.0 中仅作为占位说明文件保留；如果你更习惯标准安装方式，也可以直接使用：

```powershell
pip install .
```

## 使用方式

在项目目录运行：

```powershell
python IconFix.py
```

常用参数：

- `-path` / `--path`
  指定扫描目录，默认是当前目录。
- `--all`
  直接处理扫描到的全部快捷方式，不再交互选择。
- `--no-elevate`
  跳过自动申请管理员权限。
- `--no-pause`
  结束后不等待按键，适合脚本化调用。
- `-V` / `--version`
  查看当前版本号。

示例：

```powershell
python IconFix.py --path "D:\Games\Shortcuts" --all
```

## 管理员权限说明

2.0 版本默认会在非管理员状态下主动申请管理员权限。这是因为以下场景常常需要更高权限：

- 修改公共桌面中的快捷方式图标
- 写入受保护目录中的图标文件
- 避免处理中途因为权限不足而失败

如果用户在系统弹窗中点击“允许”，程序会自动以管理员身份重新启动并继续执行；如果点击“取消”，程序会给出明确提示并停止继续操作。

## 项目结构

```text
IconFix.py
iconfix/
  __init__.py
  cli.py
  constants.py
  elevation.py
  logging_utils.py
  models.py
  scanner.py
  shortcut.py
  steam.py
  workflow.py
tests/
docs/
```

## 测试

```powershell
python -m unittest discover -s tests -v
```

## CI/CD

仓库已经内置 GitHub Actions 工作流：

- `pull_request -> main`
  自动运行测试，作为 CI。
- `push -> main`
  自动运行测试、打包 `IconFix.exe`，然后发布到 GitHub `Prerelease`。
- `push tag -> v*`
  自动运行测试、打包 `IconFix.exe`，然后发布到 GitHub 正式 `Release`。
- `workflow_dispatch`
  支持在 GitHub 页面手动触发。

工作流文件位置：

- [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml)
- [.github/workflows/release.yml](.github/workflows/release.yml)

首次启用前建议检查仓库设置：

1. 在仓库 `Settings -> Actions -> General` 中允许 Actions 运行。
2. 确认工作流权限允许写入仓库内容，以便自动创建 Release。

正式版发布方式：

1. 先把 [iconfix/__init__.py](iconfix/__init__.py) 里的 `__version__` 更新为目标版本，例如 `2.1.0`。
2. 推送代码到 `main`，让 `Prerelease` 流程先跑通。
3. 创建并推送同名标签，例如 `v2.1.0`。

示例：

```powershell
git tag v2.1.0
git push origin v2.1.0
```

注意：

- 正式版工作流会校验 Git 标签是否与代码中的版本号一致。
- 如果标签是 `v2.1.0`，那么 `__version__` 也必须是 `2.1.0`，否则工作流会主动失败。

## 学习资料

2.0 版本的重构说明和优化思路已经整理到：

- [docs/optimization-notes-v2.0.md](docs/optimization-notes-v2.0.md)
