from httpx import Client
from discord_webhook import DiscordWebhook, DiscordEmbed
from config import FieldManager, Settings
from datetime import datetime

from concurrent.futures import ThreadPoolExecutor, Future
from dearpygui import dearpygui as dpg


class DiscordUser:
    def __init__(self, json: dict[str, str]) -> None:
        self.id: str = json["id"]
        self.created_at: str = json["created_at"]
        self.global_name: str = json["global_name"]
        self._tag: str = json["tag"]
        self.avatar_id: str = json["avatar"]["id"]
        self.avatar_is_animated: bool = json["avatar"]["is_animated"]

    @property
    def avatar_url(self):
        return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar_id}"

    @property
    def tag(self):
        return self._tag.rstrip("#0")


def request(discordID: str) -> DiscordUser:
    with Client() as client:
        data = client.get(f"https://discordlookup.mesavirep.xyz/v1/user/{discordID}").json()
    return DiscordUser(data)


def execute(data: FieldManager, settings: Settings) -> str:
    """Used to execute the posting of a victim to the wall of shame"""
    user = request(data.discordID)
    # I Only Made Reason Multiline so that the text would be readable to the user and easier to control...
    embed = DiscordEmbed(description=data.reason.replace("\n", " "))
    embed.set_author(name=user.global_name, icon_url=user.avatar_url)
    embed.set_timestamp(datetime.now())
    embed.set_color(0x282828)
    if data.photo:
        # We have a photo to go with our entry so hang it 
        # up to see the victim's stupidity in action...
        embed.set_image(data.photo)

    # TODO: Add An Option that pings everyone about a new victim added to the list...
    # Pickup the custom fields that we would like to use...
    embed.add_embed_field("discordID", user.id)
    embed.add_embed_field("global name", user.global_name)
    embed.add_embed_field("tag", user.tag)
    for f in data.fields:
        embed.add_embed_field(name=f.name, value=f.value)

    # Setup rate_limit_retry incase there's a delay or technical issue on the other side's end...
    webhook = DiscordWebhook(settings.webhook, rate_limit_retry=True)
    webhook.add_embed(embed=embed)
    webhook.execute()
    return user.tag


class TaskManager:
    def __init__(self) -> None:
        self.te = ThreadPoolExecutor()
        # Inspired by Robtop's C++ code for "GameLevelManager" The I reverse engineered recently...
        self.active_dls: dict[str, Future[str]] = {}
        self.popup_manager = []
        self.popup_idx = 0

    def isDLActive(self, dl: str) -> bool:
        return dl in list(self.active_dls.keys())

    def post_user(self, data: FieldManager, settings: Settings):
        if not self.isDLActive(data.discordID):
            self.active_dls[data.discordID] = self.te.submit(execute, data, settings)

    def popup_window(self, title: str, reason: str):
        tag = "popup_id_%i" % self.popup_idx

        def remove_window():
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag)
        
        with dpg.mutex():
            with dpg.window(tag=tag, label=title, no_close=True) as item:
                # TODO Add green and red tab windows to Signal errors and passing...
                dpg.add_text(reason, parent=item)
                dpg.add_button(label="ok", callback=remove_window)

        self.popup_idx += 1

    def render(self):
        """Used to be renedered via waiting upon active downloads..."""
        # Try to do a fast exit if possible...
        if not self.active_dls:
            return

        items = list(self.active_dls.items())
        for name, f in items:
            if f.done():
                try:  # this will remove the awaiting message from the stack if also finished
                    result = self.active_dls.pop(name).result()
                    self.popup_window(
                        "Success",
                        f"{result}'s entry was submitted\nto The Wall Of Shame!",
                    )
                except Exception as e:
                    print(e)
                    self.popup_window(f"Error: {e.__class__.__name__}", str(e))
