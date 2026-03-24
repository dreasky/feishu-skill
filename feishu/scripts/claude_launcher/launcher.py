"""
Claude Code 启动器
支持跨平台（Windows/Linux）在新窗口中启动 Claude CLI
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Literal

# 支持的权限模式
PermissionMode = Literal[
    "acceptEdits", "bypassPermissions", "default", "dontAsk", "plan", "auto"
]


class ClaudeLauncher:
    """Claude Code 启动器"""

    def __init__(self, workdir: Optional[str] = None):
        """
        初始化启动器

        Args:
            workdir: 工作目录，默认当前目录
        """
        self._workdir = Path(workdir) if workdir else Path.cwd()
        self._claude_path: Optional[str] = None

    @property
    def workdir(self) -> Path:
        return self._workdir

    @workdir.setter
    def workdir(self, value: str) -> None:
        self._workdir = Path(value)

    @property
    def claude_path(self) -> str:
        """获取 Claude CLI 路径（延迟查找）"""
        if self._claude_path is None:
            self._claude_path = self._find_claude_path()
        return self._claude_path

    def _find_claude_path(self) -> str:
        """查找 Claude CLI 路径"""
        if sys.platform == "win32":
            result = subprocess.run(
                ["where", "claude"], capture_output=True, text=True, shell=True
            )
        else:
            result = subprocess.run(["which", "claude"], capture_output=True, text=True)

        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
        return "claude"

    def _get_linux_terminal(self) -> list:
        """检测可用的 Linux 终端模拟器"""
        terminals = [
            ("gnome-terminal", ["gnome-terminal", "--"]),
            ("konsole", ["konsole", "-e"]),
            ("xfce4-terminal", ["xfce4-terminal", "-e"]),
            ("mate-terminal", ["mate-terminal", "-e"]),
            ("xterm", ["xterm", "-e"]),
        ]

        for name, cmd in terminals:
            result = subprocess.run(["which", name], capture_output=True)
            if result.returncode == 0:
                return cmd

        return ["xterm", "-e"]

    def _create_temp_script(
        self,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        permission_mode: Optional[PermissionMode] = "acceptEdits",
    ) -> str:
        """创建临时启动脚本，返回脚本路径"""
        workdir = self._workdir.resolve()

        # 构建 claude 命令
        claude_cmd = (
            f'"{self.claude_path}"' if sys.platform == "win32" else self.claude_path
        )
        if model:
            claude_cmd += f" --model {model}"
        if permission_mode:
            claude_cmd += f" --permission-mode {permission_mode}"
        if prompt:
            escaped_prompt = prompt.replace(
                '"', '""' if sys.platform == "win32" else '\\"'
            )
            claude_cmd += f' "{escaped_prompt}"'

        if sys.platform == "win32":
            content = f'@echo off\ncd /d "{workdir}"\n{claude_cmd}\n'
            suffix = ".bat"
        else:
            content = f'#!/bin/bash\ncd "{workdir}"\n{claude_cmd}\nexec bash\n'
            suffix = ".sh"

        script_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, encoding="utf-8"
        )
        script_file.write(content)
        script_file.close()

        if sys.platform != "win32":
            os.chmod(script_file.name, 0o755)

        return script_file.name

    def launch(
        self,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        permission_mode: Optional[PermissionMode] = "acceptEdits",
        new_window: bool = True,
    ) -> bool:
        """
        启动 Claude

        Args:
            prompt: 初始消息
            model: 指定模型
            permission_mode: 权限模式（默认 acceptEdits）
            new_window: 是否在新窗口启动

        Returns:
            是否启动成功
        """
        try:
            if new_window:
                return self._launch_in_new_window(prompt, model, permission_mode)
            else:
                return self._launch_in_current(prompt, model, permission_mode)
        except Exception as e:
            print(f"启动失败: {e}")
            return False

    def _launch_in_new_window(
        self,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        permission_mode: Optional[PermissionMode] = "acceptEdits",
    ) -> bool:
        """在新窗口中启动"""
        script_path = self._create_temp_script(prompt, model, permission_mode)

        if sys.platform == "win32":
            subprocess.run(
                f'start "Claude Code - {self._workdir.name}" cmd /k "{script_path}"',
                shell=True,
            )
        else:
            terminal_cmd = self._get_linux_terminal()
            subprocess.Popen(terminal_cmd + [script_path], start_new_session=True)

        return True

    def _launch_in_current(
        self,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        permission_mode: Optional[PermissionMode] = "acceptEdits",
    ) -> bool:
        """在当前窗口启动"""
        cmd = [self.claude_path]
        if model:
            cmd.extend(["--model", model])
        if permission_mode:
            cmd.extend(["--permission-mode", permission_mode])
        if prompt:
            cmd.append(prompt)

        process = subprocess.Popen(
            cmd, cwd=str(self._workdir), shell=(sys.platform == "win32")
        )
        process.wait()
        return process.returncode == 0