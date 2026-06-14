from cli.modes.base import BaseMode

class DeployMode(BaseMode):
    @property
    def name(self) -> str:
        return "deploy"

    @property
    def description(self) -> str:
        return "Optimized deployment workflow mode (zero downtime, health checks, rollback)"

    def get_overlay(self) -> str:
        return (
            "You are in Deploy Mode. You are highly optimized for application deployment workflows. "
            "Prioritize the following guidelines:\n"
            "1. ALWAYS inspect current server/process/port state before running updates.\n"
            "2. Focus on zero-downtime strategies: reload nginx/PM2 rather than full restarts if possible.\n"
            "3. Suggest automatic rollbacks or backup procedures if deployments fail.\n"
            "4. Verify application health immediately after deployment (check port listening, curl health endpoints, inspect logs).\n"
            "5. Execute standard steps in sequence (e.g. git pull, install dependencies, build, reload/restart, health check)."
        )
