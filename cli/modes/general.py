from cli.modes.base import BaseMode

class GeneralMode(BaseMode):
    @property
    def name(self) -> str:
        return "general"

    @property
    def description(self) -> str:
        return "Default balanced mode: diagnose, configure, monitor, deploy"

    def get_overlay(self) -> str:
        return (
            "You are in General Mode. This is a balanced mode. Your goal is to analyze the user's request, "
            "and suggest commands that accurately configure, diagnose, monitor, or manage the server based on "
            "what the user asks. Balance caution with utility. Always explain your plan clearly."
        )
