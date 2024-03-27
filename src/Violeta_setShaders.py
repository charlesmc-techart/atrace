import maya.cmds as cmds


def main():
    def addAttr(node, name, type_, niceName=None):
        kwargs = {"longName": name, "attributeType": type_}
        if niceName:
            kwargs["niceName"] = niceName
        try:
            cmds.addAttr(node, **kwargs)
        except:
            pass

    def connectAttr(source, destination):
        cmds.connectAttr(
            f"Violeta_{source}", f"Violeta_{destination}", force=True
        )

    sg = [
        sg
        for sg in cmds.ls("*sg", type="shadingEngine")
        if cmds.listConnections(sg, type="mesh")
    ][0]
    addAttr(sg, name="model", type_="message")
    sg = cmds.rename(sg, "Violeta_body_sg")

    hair = "Violeta_hair_sg"
    cmds.sets(renderable=True, name=hair, empty=True)
    addAttr(hair, name="model", type_="message")
    cmds.select("Hair_Meshes_grp", replace=True)
    cmds.hyperShade(assign=hair)

    for attribute, value in {
        "container": ("Shader Network", "shaderNetwork"),
        "bodyShadingEngine": ("Body Shading Group", "body_sg"),
        "bodyAiLambert": ("Body Lambert", "body_lam"),
        "bodyAiToon": ("Body Toon", "body_toon"),
        "hairShadingEngine": ("Hair Shading Group", "hair_sg"),
        "hairAiLambert": ("Hair Lambert", "hair_lam"),
        "hairAiToon": ("Hair Toon", "hair_toon"),
        "aiImage": ("Texture", "tex"),
        "aiRange": ("Line Width Limiter", "rng"),
        "aiMultiply": ("Line Width", "lineWidth"),
        "aiCellNoise": ("Line Noise", "lineNoise"),
        "aiRampRgb": ("Cel Shade", "celShade"),
    }.items():
        addAttr(
            "Violeta_Rig_grp",
            name=attribute,
            niceName=value[0],
            type_="message",
        )
        connectAttr(f"Rig_grp.{attribute}", f"{value[1]}.model")

        if attribute == "bodyAiLambert":
            connectAttr(f"{value[1]}.outColor", "body_sg.aiSurfaceShader")
        elif attribute == "bodyAiToon":
            connectAttr(f"{value[1]}.outColor", "body_sg.surfaceShader")
        elif attribute == "hairAiLambert":
            connectAttr(f"{value[1]}.outColor", "hair_sg.aiSurfaceShader")
        elif attribute == "hairAiToon":
            connectAttr(f"{value[1]}.outColor", "hair_sg.surfaceShader")

    for lam in cmds.ls(type="aiLambert"):
        if not cmds.listConnections(lam, type="shadingEngine"):
            cmds.delete(lam)

    for toon in cmds.ls(type="aiToon"):
        if not cmds.listConnections(toon, type="aiLambert"):
            cmds.delete(toon)

    for tex in cmds.ls(type=("file", "aiRampRgb", "aiCellNoise", "aiFlat")):
        if not cmds.listConnections(tex, type="aiToon"):
            cmds.delete(tex)

    cmds.delete("connectShaderNetwork_script", cmds.ls("*sceneConfiguration*"))


main()
del main
