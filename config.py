from dearpygui import dearpygui as dpg
from dataclasses import dataclass, asdict, field
import orjson


@dataclass
class Settings:
    """BasePlate for making settings..."""

    webhook: str = ""

    def set_item_event(self, name: str):
        """enforces dearpygui to pass configurations off to use elsewhere...
        this can also act as lazy bypass method..."""
        return lambda s, data: self.__setattr__(name, data)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_file(cls, filename: str):
        try:
            return cls.from_dict(orjson.loads(open(filename, "rb").read()))
        except:
            return cls.from_dict({})

    def save(self, filename: str):
        open(filename, "wb").write(orjson.dumps(self.to_dict()))


@dataclass
class Field:
    """Used to Define a discord embed Field"""

    id: int = 0
    name: str = ""
    value: str = ""
    deleted: bool = False

    def __hash__(self) -> int:
        return hash(self.group)

    def set_item_event(self, name: str):
        """enforces dearpygui to pass configurations off to use elsewhere...
        this can also act as lazy bypass method..."""
        return lambda s, data: self.__setattr__(name, data)

    @property
    def group(self):
        return "group_%i" % self.id

    def render(self):
        """Used for rendering attributes on the stack"""
        with dpg.group(parent="user-entry", tag=self.group):
            dpg.add_input_text(
                label="name",
                parent=self.group,
                default_value=self.name,
                callback=self.set_item_event("name"),
            )
            dpg.add_input_text(
                label="value",
                parent=self.group,
                default_value=self.value,
                callback=self.set_item_event("value"),
            )
            dpg.add_button(
                label="delete field", parent=self.group, callback=self.destory
            )

    def destory(self):
        """Used for destorying items"""
        if dpg.does_item_exist(self.group):
            dpg.delete_item(self.group)
            # set the flag to have the manager come by and remove our field...
            self.deleted = True


@dataclass
class FieldManager:
    """An Entry used for making webhooks with"""

    discordID: str = ""
    reason: str = ""
    photo: str = ""
    idx: int = 0
    fields: list[Field] = field(default_factory=list)

    def create(self):
        self.idx += 1
        f = Field(self.idx)
        f.render()
        return f

    def setup(self):
        with dpg.group(parent="user-entry"):
            dpg.add_input_text(
                label="DiscordID Of User",
                decimal=True,
                callback=self.set_item_event("discordID"),
            )
            dpg.add_button(label="Add Field", callback=self.newField)

    def render(self):
        removed = []
        for f in self.fields:
            if f.deleted:
                removed.append(f)

        for r in removed:
            self.fields.remove(r)

        # We should have at least 1 field avalible to us even if it's empty
        # if len(self.fields) < 1:
        #     self.fields.append(self.create())

    def set_item_event(self, name: str):
        """enforces dearpygui to pass configurations off to use elsewhere...
        this can also act as lazy bypass method..."""
        return lambda s, data: self.__setattr__(name, data)

    def newField(self):
        """Callback for making new fields to our dox entry..."""
        self.fields.append(self.create())
