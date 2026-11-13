"""Smoke PoC for #19: MlxRender + MenuScene (no App wiring).

Run from repo root (needs a working DISPLAY / WSLg):

    poetry run python -m app.render.smoke_menu

Keys: arrows move/edit, Esc quits.
"""

from __future__ import annotations

from app.render.mlx_render import MlxRender
from app.render.render_contract import IntervalChanged, Quit, ThemeChanged
from app.runtime_settings import RuntimeSettings
from app.scenes.menu_scene import MenuScene
from app.theme.catalog import default_theme, get_theme
from app.theme.theme import Theme


class _SmokeSession:
    """Tiny stand-in for App.handle_action while testing the renderer."""

    def __init__(self) -> None:
        self.settings = RuntimeSettings()
        self.theme: Theme = default_theme()
        self.menu = MenuScene(self.settings, self.theme)
        self.renderer = MlxRender(
            width=500,
            height=500,
            window_title="A-Maze-Ing (smoke menu)",
            on_action=self.handle_action,
        )

    def handle_action(
        self,
        action: ThemeChanged | IntervalChanged | Quit | object,
    ) -> None:
        if isinstance(action, Quit):
            self.renderer.request_quit()
        elif isinstance(action, ThemeChanged):
            self.settings = self.settings.with_theme(action.theme)
            self.theme = get_theme(action.theme)
            self.menu.update_settings(self.settings, self.theme)
        elif isinstance(action, IntervalChanged):
            self.settings = self.settings.with_interval(action.seconds)
            self.menu.update_settings(self.settings, self.theme)

    def run(self) -> None:
        self.renderer.initialize()
        self.renderer.set_scene(self.menu)
        print(
            "Smoke menu running. Arrows: navigate/edit. Esc: quit.",
            flush=True,
        )
        self.renderer.run()


def main() -> None:
    _SmokeSession().run()


if __name__ == "__main__":
    main()
