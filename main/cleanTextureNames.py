"""Remove the ' (1)' in certain filenames when Google Drive errors during sync"""

from pathlib import Path

import maya.cmds as cmds


def main():
    toRemove = " (1)"

    texture = cmds.getAttr("::PokemonPlush_shaderNetwork.texture")

    dir = Path(texture).parent
    toClean = (f for f in dir.iterdir() if f.is_file() and toRemove in f.stem)
    for f in toClean:
        f.rename(f"{f}".replace(toRemove, ""))


if __name__ == "__main__":
    main()
