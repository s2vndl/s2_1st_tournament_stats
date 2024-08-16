import datetime
from typing import List

W_CHAINSAW = "Chainsaw"

W_KNIFE = "Knife"

W_MAKAROV = "Makarov"

W_RPG = "RPG"

W_MINIGUN = "Minigun"
W_RM = "Rheinmetall"
W_RL = "RocketLauncher"
W_BARRETT = "Barrett"
W_DRAGUNOV = "Dragunov"
W_M79 = "M79"
W_SPASS = "Spas12"
W_AK = "Kalashnikov"
W_STEYR = "SteyrAUG"
W_MP5 = "MP5"
W_DEAGLES = "Deagles"

WEAPONS_PRIMARY = [
    W_DEAGLES,
    W_MP5,
    W_STEYR,
    W_AK,
    W_SPASS,
    W_M79,
    W_DRAGUNOV,
    W_BARRETT,
    W_RL,
    W_RM,
    W_MINIGUN,
]

WEAPONS_SECONDARY = [
    W_CHAINSAW,
    W_KNIFE,
    W_MAKAROV,
    W_RPG,
]

WEAPONS_OTHER = [
    "Melee",
    "N/A",
    "RGD5",
]
WEAPONS = WEAPONS_PRIMARY + WEAPONS_SECONDARY + WEAPONS_OTHER

WEAPON_MODS_DATES = [
    datetime.datetime(2024, 8, 4, 19, 00),
]


class WeaponMod:
    def __init__(self, date: datetime.datetime, changes: str, changes_url):
        self.changes_url = changes_url
        self.changes = changes.strip()
        self.datetime = date

    def __str__(self):
        return 'WeaponMod ' + self.datetime.strftime("%Y-%m-%d")


class WeaponModCatalog:
    def __init__(self, wms: List[WeaponMod]):
        self.wms = wms

    def latest(self):
        return self.wms[0]

    def previous(self, n=1):
        return self.wms[n]


WEAPON_MODS = [
    WeaponMod(datetime.datetime(2024, 8, 4, 19, 00), """
loads of changes =.=
""", "no link"),
    ]

WEAPON_MODS_CATALOG = WeaponModCatalog(WEAPON_MODS)
