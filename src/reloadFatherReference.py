import maya.cmds as cmds


def reloadFather():
    ref = [node for node in cmds.ls(type="reference") if node.startswith("father")][0]
    filepath = cmds.referenceQuery(ref, filename=True)
    cmds.file(filepath, unloadReference=True)
    cmds.file(filepath, loadReference=True)


reloadFather()
