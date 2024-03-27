import maya.cmds as cmds

coinModel = "::Coin_geo"
if cmds.referenceQuery(coinModel, isNodeReferenced=True):

    def connectToMasterShaders():
        coinNetwork = "::Coin_"
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
                    f"{coinModel}.{source}",
                    f"{coinNetwork}{destination}.model",
                    force=True,
                )
            except RuntimeError:
                pass

        cmds.select(coinModel, replace=True)
        try:
            cmds.hyperShade(assign=f"{coinNetwork}sg")
        except:
            pass
        cmds.select(clear=True)

    connectToMasterShaders()

del coinModel
