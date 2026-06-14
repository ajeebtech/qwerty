from cli.modes.base import BaseMode

class DebugMode(BaseMode):
    @property
    def name(self) -> str:
        return "debug"

    @property
    def description(self) -> str:
        return "Incident & diagnostic debug mode (logs, resource pressure, network, config)"

    def get_overlay(self) -> str:
        return (
            "You are in Debug Mode. You are focused on diagnosing incidents and troubleshooting server errors. "
            "Prioritize the following guidelines:\n"
            "1. ALWAYS inspect relevant system and app logs first (e.g. journalctl, nginx error logs, pm2 logs, tail last 100 lines).\n"
            "2. Investigate recent changes (e.g., git status/log, systemctl status, files modified in last 24h).\n"
            "3. Assess resource pressure (CPU, RAM, free disk space, open file descriptors).\n"
            "4. Analyze network status (listening ports with ss/netstat, ufw/iptables firewall rules).\n"
            "5. Formulate hypotheses and collect diagnostic evidence BEFORE suggesting configuration modifications or fixes."
        )
