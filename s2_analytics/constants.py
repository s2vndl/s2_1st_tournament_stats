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
    datetime.datetime(2023, 3, 5),
    datetime.datetime(2022, 12, 28),
]


class WeaponMod:
    def __init__(self, date: datetime.datetime, changes: str):
        self.changes = changes
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
    WeaponMod(datetime.datetime(2023, 3, 20), """
        - Rocket Launcher has lower kickback ("self-push")
        - Rocket Launcher has lower bullet force (impact when hitting other players)
        - Increased minimum dropkick ("headbutt") velocity in attempt to fix low-velocity player collision/bumping
        - Steyr &  Kalashnikov have a bit more bullet force
        """),
    WeaponMod(datetime.datetime(2023, 3, 5), """
    - Dragunov
        faster interval (0.7s -> 0.67s)
        Clip increased (6 -> 7)
        Reloadtime decreased (2.7s -> 2.5s)
        15% more head damage
        12% more leg damage
        better accuracy & less movement inaccuracy 

    - Spas-12
        less self-boost
        faster reload (0.45s -> 0.4s)

    - M79
        boost forces decreased
        less splash damage
        slightly more reloadtime (2.9s -> 3.0s)

    - RPG
        boost forces decreased

    - Kalashnikov & Steyr-AUG
        more bullet penetration

    - MP5
        slightly less head damage
        slightly less leg damage
        Reloadtime increased (1.9s -> 2.0s)

    - Barret
        no longer 'autoreloads' when not equipped

    - Makarov
        slightly lower reloadtime (1.4s -> 1.3s)

    - Knife
        no random kills from nearby explosions

    - Minigun
        Clip increased (90 -> 100)

    - Flag forces
        various improvements"""),
    WeaponMod(datetime.datetime(2022, 12, 28), """
    - Mp5, Steyr, AK damage reduced
    - Body-part damage modifiers added
    """),
]

WEAPON_MODS_CATALOG = WeaponModCatalog(WEAPON_MODS)
