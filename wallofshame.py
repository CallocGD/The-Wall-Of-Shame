from dearpygui import dearpygui as dpg
from contextlib import contextmanager
from typing import Union, Callable, TypeVar
from config import Settings, FieldManager
from userlookup import TaskManager


T = TypeVar("T")


class GUIContext:
    """Used to help make the top windows of dearpygui"""

    def __init__(self, title: str, width: int, height: int, **kw) -> None:
        dpg.create_context()
        dpg.create_viewport(title=title, width=width, height=height, **kw)
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def __enter__(self):
        return self

    @contextmanager
    def main_window(self, label: str, **kw):
        """Automatically makes and sets up a main window to use..."""
        with dpg.window(label=label, **kw) as w:
            yield w
        dpg.set_primary_window(w, True)

    def tooltip(self, obj: Union[int, str], text: str, **kw):
        with dpg.tooltip(obj):
            dpg.add_text(text, **kw)
        return obj

    def __exit__(self, *args):
        dpg.destroy_context()


class Context(GUIContext):
    """Used as the Main Context in the program"""

    def __init__(self, title: str, width: int, height: int, **kw) -> None:
        super().__init__(title, width, height, **kw)
        self.settings = Settings.from_file("settings.json")
        self.field_manager = FieldManager()
        self.tm = TaskManager()

    def main(self):
        with self.main_window(label="The Wall of Shame"):
            with dpg.menu_bar():
                with dpg.menu(label="settings") as settings:
                    with dpg.menu(label="set discord webhook") as webhook:
                        dpg.add_input_text(
                            label="discord webhook url",
                            default_value=self.settings.webhook,
                            callback=self.settings.set_item_event("webhook"),
                        )
            dpg.add_text("Welcome to the Wall of Shame...")
            with dpg.child_window(tag="user-entry", height=100):
                self.field_manager.setup()
            dpg.add_text("Images of Offence or proof they happened")
            dpg.add_input_text(
                label="Url of Photo",
                default_value=self.field_manager.photo,
                callback=self.field_manager.set_item_event("photo"),
            )
            dpg.add_text("Reason For Entry")
            dpg.add_input_text(
                multiline=True,
                default_value=self.field_manager.reason,
                callback=self.field_manager.set_item_event("reason"),
            )
            dpg.add_button(label="Submit Entry", callback=lambda:self.tm.post_user(self.field_manager, self.settings))


    def render(self):
        while dpg.is_dearpygui_running():
            self.field_manager.render()
            self.tm.render()
            dpg.render_dearpygui_frame()

    def __exit__(self, *args):
        self.settings.save("settings.json")
        return super().__exit__(*args)


if __name__ == "__main__":
    with Context("The Wall of Shame", 500, 400) as ctx:
        ctx.main()
        ctx.render()
