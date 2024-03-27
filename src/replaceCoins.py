import maya.cmds as cmds


def main():
    coins = cmds.listRelatives(
        "back_coins", allDescendents=True, type="mesh", fullPath=True
    )
    coins = cmds.listRelatives(coins, parent=1, fullPath=True)
    newGroup = cmds.group(name="new_coins", empty=True, world=True)

    for coin in coins:
        position = cmds.xform(
            coin, query=True, translation=True, worldSpace=True
        )
        x, y, z = cmds.xform(coin, query=True, rotation=True, worldSpace=True)
        x += 90
        orientation = x, y, z
        newCoin = cmds.instance("Coin_geo")
        cmds.xform(
            newCoin, translation=position, rotation=orientation, worldSpace=True
        )
        cmds.parent(newCoin, newGroup)

    cmds.delete("back_coins")


if __name__ == "__main__":
    main()
