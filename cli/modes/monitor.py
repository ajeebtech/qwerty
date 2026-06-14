from cli.modes.base import BaseMode

class MonitorMode(BaseMode):
    @property
    def name(self) -> str:
        return "monitor"

    @property
    def description(self) -> str:
        return "Passive monitoring mode (read-only diagnostics, server health summary)"

    def get_overlay(self) -> str:
        return (
            "You are in Monitor Mode. This is a passive monitoring mode. "
            "Prioritize the following guidelines:\n"
            "1. ONLY run read-only commands (e.g. status, free, df, uptime, top/htop stats, netstat/ss, tailing logs).\n"
            "2. Under no circumstances suggest write commands or modifying system/config files unless the user explicitly requests a write command.\n"
            "3. Summarize server health status, showing CPU, memory, disk usage, active services, and open connections."
        )
