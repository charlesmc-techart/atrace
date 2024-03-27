import maya.cmds as cmds


def setUVPinMatrix():
    cmds.undoInfo(openChunk=True)

    # Get all locators under `face_controls_grp`
    locators = cmds.ls(selection=True, transforms=True)

    # Loop through each locator
    for locator in locators:
        # Get group under locator + unPin connected to it
        group = cmds.listRelatives(locator, children=True, type="transform")[0]
        pin = cmds.listConnections(locator, source=True, type="uvPin")[0]

        # Establish node names
        locatorName = group.replace("grp", "loc")
        pinName = group.replace("grp", "uvPin")
        pickMatrixName = group.replace("grp", "mtx")

        # Rename nodes
        cmds.rename(locator, locatorName)
        cmds.rename(pin, pinName)

        # Create pickMatrix
        pickMatrix = cmds.createNode("pickMatrix", name=pickMatrixName)
        for attribute in "useRotate", "useScale", "useShear":
            cmds.setAttr(f"{pickMatrix}.{attribute}", False)

        # Connect pickMatrix
        cmds.parent(f"{locatorName}|{group}", world=True)

        cmds.connectAttr(
            f"{pinName}.outputMatrix[0]", f"{pickMatrixName}.inputMatrix", force=True
        )
        cmds.connectAttr(
            f"{pickMatrixName}.outputMatrix",
            f"{locatorName}.offsetParentMatrix",
            force=True,
        )

        cmds.parent(f"|{group}", locatorName)

        # Hide locator
        cmds.setAttr(f"{locatorName}Shape.visibility", False)

    cmds.undoInfo(closeChunk=True)


setUVPinMatrix()
