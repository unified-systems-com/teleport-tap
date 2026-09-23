"""TAP Teleport plugin AppConfig — the base ready() registers the manifest; this one adds the
plugin's panel type (req-teleport-panel-board)."""

from tap_plugins.base import TapPluginConfig


class TeleportConfig(TapPluginConfig):
    def ready(self) -> None:
        super().ready()
        from tap_plugin.teleport.panels.board import TeleportBoardPanelType

        from tap_web.registry import panel_type_registry

        panel_type_registry.register(TeleportBoardPanelType.slug, TeleportBoardPanelType)
