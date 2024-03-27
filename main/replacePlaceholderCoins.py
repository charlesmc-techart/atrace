from functools import partial

import maya.cmds as cmds

"""Replace the 100+ placeholder coin models with the finalized model"""


def main() -> None:
    oldGroup = "back_coins"
    newGroup = cmds.group(name="new_coins", empty=True, world=True)
    newCoin = "Coin_geo"

    listRelativesCmd = partial(cmds.listRelatives, fullPath=True)
    coins = listRelativesCmd(oldGroup, allDescendents=True, type="mesh")
    coins = listRelativesCmd(coins, parent=True)

    xformCmd = partial(cmds.xform, worldSpace=True)
    for c in coins:
        position = xformCmd(c, query=True, translation=True)
        x, y, z = xformCmd(c, query=True, rotation=True)
        x += 90
        orientation = x, y, z
        newCoin = cmds.instance(newCoin)
        xformCmd(newCoin, translation=position, rotation=orientation)
        cmds.parent(newCoin, newGroup)

    cmds.delete(oldGroup)


if __name__ == "__main__":
    main()
