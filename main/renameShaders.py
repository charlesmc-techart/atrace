import maya.cmds as cmds

"""Rename the shaders in the network to match the geometry's"""


def main():
    suffixes = (
        "shaderNetwork",
        "sg",
        "lam",
        "toon",
        "tex",
        "rng",
        "lineWidth",
        "lineNoise",
    )

    networks = (c for c in cmds.ls("*shaderNetwork", type="container"))
    for n in networks:
        model = cmds.listConnections(f"{n}.model")[0]
        oldName = n.rsplit("_shaderNetwork", 1)[0]
        newName = model.replace("_grp", "").replace("_geo", "")

        shaders = (
            s
            for s in cmds.listConnections(model)
            if s.rsplit("_", 1)[-1] in suffixes
        )
        for s in shaders:
            cmds.rename(s, s.replace(oldName, newName))


if __name__ == "__main__":
    main()
