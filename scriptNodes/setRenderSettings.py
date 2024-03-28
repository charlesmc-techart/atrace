"""Set the necessary render settings when the file is opened"""

from functools import partial
from itertools import count

import maya.cmds as cmds

cmds.loadPlugin("mtoa", quiet=True)
import mtoa


def setRenderSettings() -> None:
    setStrAttr = partial(cmds.setAttr, type="string")

    for network in cmds.ls("::*_shaderNetwork", type="container"):
        try:
            texture = cmds.getAttr(f"{network}.texture")
        except ValueError:
            continue
        if not texture:
            continue

        filename = texture.rsplit("/", 1)[-1]
        setStrAttr(f"{network}.texture", f"sourceimages/{filename}")

    default = "defaultRenderGlobals"
    setStrAttr(f"{default}.currentRenderer", "arnold")

    prefix = cmds.getAttr(f"{default}.imageFilePrefix")
    if (not prefix) or len(prefix) <= 3 or (not prefix.startswith("ACT")):
        filename = cmds.file(query=True, sceneName=True, shortName=True)
        if "ACT" in filename:
            start = filename.index("ACT")
            act = filename[start:][3]
            shot = filename[start:][5:7]
            setStrAttr(f"{default}.imageFilePrefix", f"ACT{act}-{shot}")

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
            cmds.setAttr(f"{camera}.mask", True)
            cmds.setAttr(f"{camera}.depth", True)
        else:
            cmds.setAttr(f"{camera}.renderable", False)

    cmds.setAttr("defaultResolution.width", 1920)
    cmds.setAttr("defaultResolution.height", 1080)

    arnold = "defaultArnold"
    setStrAttr(f"{arnold}Driver.aiTranslator", "exr")

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
        setStrAttr(f"{arnold}RenderOptions.textureAutoTxPath", directory)
    except RuntimeError:
        pass

    setStrAttr(f"{arnold}Filter.aiTranslator", "contour")

    outlinerEditorCmd = partial(cmds.outlinerEditor, edit=True)
    for n in count(start=1):
        try:
            outlinerEditorCmd(f"outlinerPanel{n}", showContainedOnly=True)
        except RuntimeError:
            break
        else:
            outlinerEditorCmd(f"outlinerPanel{n}", showNamespace=False)

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

        def isZOrId(aov: str) -> bool:
            return aov == "Z" or aov == "ID"

        connectAttrCmd = partial(cmds.connectAttr, force=True)
        for aov in aovs:
            name = f"aiAOV_{aov}"
            if not (
                cmds.objExists(name) and cmds.objectType(name, isType="aiAOV")
            ):
                if isZOrId(aov):
                    aovint.addAOV(aov)
                else:
                    aovint.addAOV(aov, aovType="rgba")

            if isZOrId(aov):
                connectAttrCmd(
                    "::closest_filter.message",
                    f"{name}.outputs[0].filter",
                )
            elif aov == "outline":
                connectAttrCmd(
                    f"{arnold}Filter.message",
                    f"{name}.outputs[0].filter",
                )
            else:
                connectAttrCmd(
                    "::box_filter.message",
                    f"{name}.outputs[0].filter",
                )
        else:
            cmds.delete(cmds.ls("aiAOVFilter*", type="aiAOVFilter"))


setRenderSettings()
