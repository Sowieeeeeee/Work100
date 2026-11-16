"""桌面提醒：本地小窗口 + 浏览器仪表盘。"""
from __future__ import annotations

import subprocess
import sys
import webbrowser
from pathlib import Path


def pythonw() -> str:
    exe = Path(sys.executable)
    candidate = exe.with_name("pythonw.exe")
    return str(candidate if candidate.exists() else exe)


def send(title: str, body: str, url: str | None = None) -> None:
    """启动一个独立的提醒窗口，不阻塞训练器。"""
    script = Path(__file__).resolve().parent.parent / "trainer.py"
    args = [pythonw(), str(script), "notify-window", title, body]
    if url:
        args.append(url)
    flags = 0x00000008 if hasattr(subprocess, "DETACHED_PROCESS") else 0
    try:
        subprocess.Popen(args, creationflags=flags, close_fds=True)
    except Exception:
        try:
            import winsound

            winsound.MessageBeep()
        except Exception:
            pass


def show_window(title: str, body: str, url: str | None = None) -> None:
    try:
        import tkinter as tk
    except Exception:
        return
    root = tk.Tk()
    root.title("Hot100 训练器")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    try:
        root.attributes("-alpha", 0.97)
    except tk.TclError:
        pass
    width, height = 390, 148
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.geometry(f"{width}x{height}+{screen_w - width - 24}+{screen_h - height - 64}")
    root.configure(bg="#101827")

    frame = tk.Frame(root, bg="#101827", highlightbackground="#2dd4bf", highlightthickness=1)
    frame.pack(fill="both", expand=True)
    tk.Label(
        frame, text=title, bg="#101827", fg="#f8fafc",
        font=("Microsoft YaHei UI", 11, "bold"), anchor="w", justify="left",
        wraplength=350,
    ).pack(fill="x", padx=14, pady=(12, 4))
    tk.Label(
        frame, text=body, bg="#101827", fg="#94a3b8",
        font=("Microsoft YaHei UI", 9), anchor="w", justify="left",
        wraplength=350,
    ).pack(fill="x", padx=14)
    row = tk.Frame(frame, bg="#101827")
    row.pack(fill="x", padx=14, pady=(8, 10))

    def close():
        root.destroy()

    def open_url():
        if url:
            webbrowser.open(url)
        close()

    tk.Button(
        row, text="知道了", command=close, bg="#1f2937", fg="#e2e8f0",
        activebackground="#374151", activeforeground="#ffffff", relief="flat",
        font=("Microsoft YaHei UI", 9), padx=12, pady=3, borderwidth=0,
    ).pack(side="right")
    if url:
        tk.Button(
            row, text="打开仪表盘", command=open_url, bg="#0d9488", fg="#ffffff",
            activebackground="#0f766e", activeforeground="#ffffff", relief="flat",
            font=("Microsoft YaHei UI", 9, "bold"), padx=12, pady=3, borderwidth=0,
        ).pack(side="right", padx=8)

    root.after(15000, close)
    root.mainloop()
