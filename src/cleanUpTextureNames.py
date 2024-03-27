import os

import maya.cmds as cmds


def main(remove: str = " (1)"):
    texture = cmds.getAttr("::PokemonPlush_shaderNetwork.texture")
    directory = os.path.dirname(texture)
    os.chdir(directory)
    sourceimages = os.listdir(directory)
    for file in (file for file in sourceimages if remove in file):
        os.rename(file, file.replace(remove, ""))


if __name__ == "__main__":
    main()
