"""
Claude Code 启动器
支持跨平台（Windows/Linux）在新窗口中启动 Claude CLI
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Literal, Tuple

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
        self._claude_cli_path: Optional[str] = None
        self._node_path: Optional[str] = None

    @property
    def workdir(self) -> Path:
        return self._workdir

    @workdir.setter
    def workdir(self, value: str) -> None:
        self._workdir = Path(value)

    def _find_claude_paths(self) -> Tuple[str, str]:
        """
        查找 node 和 Claude CLI 的路径

        Returns:
            (node_path, cli_js_path)
        """
        if sys.platform == "win32":
            # 查找 claude.cmd 的位置
            result = subprocess.run(
                ["where", "claude.cmd"], capture_output=True, text=True, shell=True
            )
            if result.returncode == 0:
                claude_cmd_path = result.stdout.strip().split("\n")[0]
                claude_dir = Path(claude_cmd_path).parent

                # 确定 node 路径
                node_exe = claude_dir / "node.exe"
                if node_exe.exists():
                    node_path = str(node_exe)
                else:
                    node_path = "node"

                # cli.js 路径
                cli_js = claude_dir / "node_modules" / "@anthropic-ai" / "claude-code" / "cli.js"
                if cli_js.exists():
                    return node_path, str(cli_js)

        # 回退：使用系统 node 和 claude 命令
        return "node", "claude"

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

        # 获取 node 和 cli.js 路径
        node_path, cli_path = self._find_claude_paths()

        if sys.platform == "win32":
            # PowerShell 脚本 - 直接用 node 执行 cli.js
            args = [f"'{cli_path}'"]
            if model:
                args.append(f"--model {model}")
            if permission_mode:
                args.append(f"--permission-mode {permission_mode}")
            if prompt:
                escaped_prompt = prompt.replace("'", "''")
                args.append(f"'{escaped_prompt}'")

            args_str = " " + " ".join(args)
            content = f"Set-Location '{workdir}'\n& '{node_path}' {args_str}\n"
            suffix = ".ps1"
        else:
            # Bash 脚本
            claude_cmd = "claude"
            if model:
                claude_cmd += f" --model {model}"
            if permission_mode:
                claude_cmd += f" --permission-mode {permission_mode}"
            if prompt:
                escaped_prompt = prompt.replace('"', '\\"')
                claude_cmd += f' "{escaped_prompt}"'

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
            # 直接启动新的 PowerShell 窗口执行脚本
            subprocess.Popen(
                [
                    "powershell",
                    "-NoExit",
                    "-ExecutionPolicy", "Bypass",
                    "-File", script_path,
                ],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
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
        node_path, cli_path = self._find_claude_paths()

        if sys.platform == "win32" and cli_path.endswith(".js"):
            cmd = [node_path, cli_path]
        else:
            cmd = ["claude"]

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