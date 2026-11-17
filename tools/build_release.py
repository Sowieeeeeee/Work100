"""打包本地可运行 release 目录 + zip。

用法：python -m tools.build_release [--version v0.4.0-p4]

产物（在 release/ 下）：
- Hot100Trainer-<version>/   自包含可运行目录
- Hot100Trainer-<version>.zip

包含：trainer.py、hot100/、tools/、assets/、README、DESIGN 文档、
      data 的 4 个数据源（problems/raw_questions/exam_pool/pool_raw）、
      已生成的 problems/ core/ reference/ 素材、启动脚本与安装说明。

排除（用户状态 / 密钥 / 构建产物，首次运行会自动重建）：
      data/state.db  data/config.json  data/secrets.json  data/online_cache.json
      data/plan_raw.json（仅 build_dataset 用）  solutions/  logs/  sessions/  __pycache__  .git
"""
from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE_DIR = ROOT / "release"

# 目录复制时跳过这些子目录
SKIP_DIRS = {"__pycache__", ".git", "logs", "sessions", "solutions"}
# data/ 下只带数据源，不带用户状态/密钥
SKIP_DATA_FILES = {"state.db", "config.json", "secrets.json", "online_cache.json", "plan_raw.json"}

LAUNCHER = """@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Hot100 Trainer
echo 正在启动 Hot100 训练台（首次启动会生成题面与计划）...
python trainer.py serve
if errorlevel 1 (
  echo.
  echo 启动失败。请确认已安装 Python 3.10+，并已把 python 加入 PATH。
  pause
)
"""

README_RELEASE = """# Hot100 训练台（本地运行版 {version}）

纯 Python 标准库实现，无需安装第三方依赖，不需要网络（考试题库为本地预置精选题库）。

## 运行

1. 确认本机装了 Python 3.10+（命令行输入 `python --version`）。
2. 双击 `启动训练台.bat`，或在命令行运行：

       python trainer.py serve

3. 浏览器会自动打开 http://127.0.0.1:8765/ （也可手动访问）。

## 常用命令

    python trainer.py status            查看今日计划
    python trainer.py serve --port 9000 换个端口启动
    python trainer.py check 1           用官方样例自测第 1 题
    python trainer.py hint 1            看第 1 题分级提示
    python trainer.py reference 1       看第 1 题参考题解

## 数据与重置

- 进度存在 data/state.db，配置在 data/config.json，均不会被打进 release。
- 想清空进度重来：`python trainer.py reset --yes`。

## 模拟考试（本地题库）

- 仪表盘顶部 tab「模拟考试」：从 300+ 道 Medium/Hard 精选题随机组卷。
- 题库来自 data/exam_pool.json + data/pool_raw.json；如需重建：
  `python -m tools.build_exam_pool.py`（需能访问 leetcode.cn）。

## 目录说明

    hot100/        程序本体（判题、计划、存储、仪表盘、激励、考试、面试）
    tools/         验证与建库脚本
    data/          题库数据源（*.json）；运行后才会出现 state.db / config.json
    problems/      题面（Markdown）
    core/          核心代码模式脚手架
    reference/     参考题解
    solutions/     你的代码（首次写题时自动生成模板）
"""


def _ignore(src_dir: str, names: list[str]) -> set[str]:
    if Path(src_dir).name == "data":
        return set(SKIP_DATA_FILES) | (SKIP_DIRS & set(names))
    return SKIP_DIRS & set(names)


def build(version: str, make_zip: bool = True) -> Path:
    out = RELEASE_DIR / f"Hot100Trainer-{version}"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    for item in ("trainer.py", "README.md", "DESIGN_v2.md", "DESIGN_v3.md",
                 "hot100", "tools", "assets", "data", "problems", "core", "reference"):
        src = ROOT / item
        if not src.exists():
            print(f"  [skip] 缺失 {item}")
            continue
        dst = out / item
        if src.is_dir():
            shutil.copytree(src, dst, ignore=_ignore)
        else:
            shutil.copy2(src, dst)

    (out / "logs").mkdir(exist_ok=True)
    (out / "sessions").mkdir(exist_ok=True)
    (out / "solutions").mkdir(exist_ok=True)
    (out / "启动训练台.bat").write_text(LAUNCHER, encoding="utf-8")
    (out / "README-RELEASE.txt").write_text(
        README_RELEASE.format(version=version), encoding="utf-8"
    )

    if make_zip:
        zip_path = RELEASE_DIR / f"Hot100Trainer-{version}.zip"
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in sorted(out.rglob("*")):
                if file.is_file():
                    zf.write(file, file.relative_to(RELEASE_DIR))
        print(f"zip  : {zip_path}")

    print(f"目录 : {out}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v0.4.0-p4")
    ap.add_argument("--no-zip", action="store_true")
    args = ap.parse_args()
    RELEASE_DIR.mkdir(exist_ok=True)
    out = build(args.version, make_zip=not args.no_zip)
    total = sum(1 for _ in out.rglob("*") if _.is_file())
    print(f"打包完成：{total} 个文件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
