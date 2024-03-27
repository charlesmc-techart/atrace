import maya.cmds as cmds


def setRenderSettings() -> None:
    """Sets the necessary render settings when the file is opened."""
    cmds.loadPlugin("mtoa", quiet=True)

    for network in cmds.ls("::*_shaderNetwork", type="container"):
        try:
            texture = cmds.getAttr(f"{network}.texture")
        except ValueError:
            pass
        else:
            if texture:
                filename = texture.rsplit("/", 1)[-1]
                cmds.setAttr(
                    f"{network}.texture",
                    f"sourceimages/{filename}",
                    type="string",
                )

    default = "defaultRenderGlobals"
    cmds.setAttr(f"{default}.currentRenderer", "arnold", type="string")

    prefix = cmds.getAttr(f"{default}.imageFilePrefix")
    if (not prefix) or len(prefix) <= 3 or (not prefix.startswith("ACT")):
        filename = cmds.file(query=True, sceneName=True, shortName=True)
        if "ACT" in filename:
            start = filename.index("ACT")
            act = filename[start:][3]
            shot = filename[start:][5:7]
            cmds.setAttr(
                f"{default}.imageFilePrefix", f"ACT{act}-{shot}", type="string"
            )

    for attribute, value in {
        "animation": True,
        "putFrameBeforeExt": True,
        "periodInExt": 2,
        "extensionPadding": 3,
    }.items():
        cmds.setAttr(f"{default}.{attribute}", value)

    for camera in cmds.ls(cameras=True):
        if camera.startswith("ACT"):
            cmds.setAttr(f"{camera}.renderable", True)
            for attribute in ("mask", "depth"):
                cmds.setAttr(f"{camera}.{attribute}", True)
        else:
            cmds.setAttr(f"{camera}.renderable", False)

    for attribute, value in {"width": 1920, "height": 1080}.items():
        cmds.setAttr(f"defaultResolution.{attribute}", value)

    arnold = "defaultArnold"
    cmds.setAttr(f"{arnold}Driver.aiTranslator", "exr", type="string")

    for attribute, value in {
        "exrCompression": 4,
        "halfPrecision": True,
        "exrTiled": True,
        "mergeAOVs": True,
        "colorManagement": 0,
    }.items():
        cmds.setAttr(f"{arnold}Driver.{attribute}", value)

    for attribute, value in {
        "AASamples": 5,
        "GIDiffuseSamples": 2,
        "GISpecularSamples": 0,
        "GITransmissionSamples": 0,
        "GISssSamples": 0,
        "GIVolumeSamples": 0,
        "enableProgressiveRender": False,
        "enableAdaptiveSampling": True,
        "AASamplesMax": 6,
        "AAAdaptiveThreshold": 0.1,
        "lock_sampling_noise": True,
        "GITotalDepth": 5,
        "GIDiffuseDepth": 1,
        "GISpecularDepth": 0,
        "GITransmissionDepth": 0,
        "GIVolumeDepth": 0,
        "autoTransparencyDepth": 5,
        "ignoreMotionBlur": True,
        "bucketScanning": 1,
        "bucketSize": 384,
        "threads_autodetect": True,
    }.items():
        cmds.setAttr(f"{arnold}RenderOptions.{attribute}", value)

    directory = cmds.internalVar(userTmpDir=True)
    try:
        cmds.setAttr(
            f"{arnold}RenderOptions.textureAutoTxPath", directory, type="string"
        )
    except RuntimeError:
        pass

    cmds.setAttr(f"{arnold}Filter.aiTranslator", "contour", type="string")

    for n in range(1, 5):
        try:
            cmds.outlinerEditor(
                f"outlinerPanel{n}", edit=True, showContainedOnly=True
            )
        except RuntimeError:
            break
        else:
            cmds.outlinerEditor(
                f"outlinerPanel{n}", edit=True, showNamespace=False
            )

    # Create AOVs when the file is referenced into a scene
    if cmds.referenceQuery("::setRenderSettings_script", isNodeReferenced=True):
        cmds.evaluationManager(mode="off")

        aovint = mtoa.aovs.AOVInterface()
        aovs = (
            "background",
            "direct",
            "indirect",
            "emission",
            "outline",
            "Z",
            "ID",
        )
        for aov in aovs:
            name = f"aiAOV_{aov}"
            if not (
                cmds.objExists(name) and cmds.objectType(name, isType="aiAOV")
            ):
                if aov in aovs[:5]:
                    aovint.addAOV(aov, aovType="rgba")
                else:
                    aovint.addAOV(aov)

            if aov == "Z" or aov == "ID":
                cmds.connectAttr(
                    f"::closest_filter.message",
                    f"{name}.outputs[0].filter",
                    force=True,
                )
            elif aov != "outline":
                cmds.connectAttr(
                    f"::box_filter.message",
                    f"{name}.outputs[0].filter",
                    force=True,
                )
            else:
                cmds.connectAttr(
                    f"{arnold}Filter.message",
                    f"{name}.outputs[0].filter",
                    force=True,
                )
        else:
            cmds.delete(cmds.ls("aiAOVFilter*", type="aiAOVFilter"))


setRenderSettings()
