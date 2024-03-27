import maya.cmds as cmds

"""Reload The Father rig when the IK leg bugs out"""


def main():
    referenceNode = cmds.ls("father*", type="reference")[0]
    filePath = cmds.referenceQuery(referenceNode, filename=True)
    cmds.file(filePath, unloadReference=True)
    cmds.file(filePath, loadReference=True)


if __name__ == "__main__":
    main()
