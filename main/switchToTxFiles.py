import maya.cmds as cmds

"""Use Arnold's TX files as textures instead of PNGs"""


def main() -> None:
    for network in cmds.ls("::*_shaderNetwork", type="container"):
        try:
            texture = cmds.getAttr(f"{network}.texture")
        except ValueError:
            continue
        else:
            if not texture:
                continue

            filename = texture.rsplit("/", 1)[-1].replace(".png", ".tx")
            cmds.setAttr(
                f"{network}.texture",
                f"sourceimages/{filename}",
                type="string",
            )


if __name__ == "__main__":
    main()
