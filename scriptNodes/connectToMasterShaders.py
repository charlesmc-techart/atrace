import maya.cmds as cmds

"""Connect a referenced rig's geometry to the master layout's shader network

Some 3D models already present in the master layout. So instead of having the
rigs have their own separate shader networks, connect the rig's geometry to the
its corresponding network.
"""

REFERENCED_RIG_GEO = "::"
MASTER_ASSET_NAME = "::"

if cmds.referenceQuery(REFERENCED_RIG_GEO, isNodeReferenced=True):

    def connectToMasterShaders():
        for source, destination in {
            "container": "shaderNetwork",
            "shadingEngine": "sg",
            "aiLambert": "lam",
            "aiToon": "toon",
            "aiRange": "rng",
            "aiMultiply": "lineWidth",
        }.items():
            try:
                cmds.connectAttr(
                    f"{REFERENCED_RIG_GEO}.{source}",
                    f"{MASTER_ASSET_NAME}{destination}.model",
                    force=True,
                )
            except RuntimeError:
                continue

        cmds.select(REFERENCED_RIG_GEO, replace=True)
        try:
            cmds.hyperShade(assign=f"{MASTER_ASSET_NAME}sg")
        except:
            pass
        cmds.select(clear=True)

    connectToMasterShaders()

del REFERENCED_RIG_GEO, MASTER_ASSET_NAME
