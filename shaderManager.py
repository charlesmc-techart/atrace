"""Create shader networks for selected objects"""

import maya.api.OpenMaya as om
import maya.cmds as cmds

# Establish master aiRampRgb, aiFlat, and aiCellNoise node names
MASTER_CEL_SHADE = "master_celShade"
MASTER_LINE_COLOR = "master_lineColor"
MASTER_LINE_NOISE = "master_lineNoise"


class Model:
    """3D model of a prop"""

    def __init__(self, longName: str) -> None:
        self.dagPath = om.MGlobal.getSelectionListByName(longName).getDagPath(0)
        self.connectToMasterLineColor = True
        self.connectToMasterLineNoise = True
        self.frame = None  # frameLayout

        for attribute, niceName in {
            "container": "Shader Network",
            "shadingEngine": "Shading Group",
            "aiLambert": "Lambert",
            "aiToon": "Toon",
            "aiImage": "Texture",
            "aiRange": "Line Width Limiter",
            "aiMultiply": "Line Width",
            "aiCellNoise": "Line Noise",
        }.items():
            if not cmds.attributeQuery(attribute, node=self, exists=True):
                cmds.addAttr(
                    self,
                    longName=attribute,
                    niceName=niceName,
                    attributeType="message",
                )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.dagPath.fullPathName()})"

    def __str__(self) -> str:
        return self.dagPath.partialPathName()

    def __eq__(self, other: str) -> bool:
        return self.dagPath.fullPathName() == other

    @property
    def display(self) -> str:
        if shapes := cmds.listRelatives(
            self.dagPath, shapes=True, fullPath=True
        ):
            type_ = cmds.objectType(shapes[0])
        else:
            type_ = "group"
        return f"{self} ({type_})".replace("|", " > ")

    @property
    def asset(self) -> str:
        try:
            return cmds.listConnections(self, type="container")[0]
        except TypeError:
            return f"{self.dagPath}_shaderNetwork".replace("|", "_")

    @property
    def shadingGroup(self) -> str:
        try:
            return cmds.listConnections(self, type="shadingEngine")[0]
        except TypeError:
            return f"{self.dagPath}_sg".replace("|", "_")

    @property
    def lambert(self) -> str:
        try:
            return cmds.listConnections(self, type="aiLambert")[0]
        except TypeError:
            return f"{self.dagPath}_lam".replace("|", "_")

    @property
    def toon(self) -> str:
        try:
            return cmds.listConnections(self, type="aiToon")[0]
        except TypeError:
            return f"{self.dagPath}_toon".replace("|", "_")

    @property
    def texture(self) -> str:
        try:
            return cmds.listConnections(self, type="aiImage")[0]
        except TypeError:
            return f"{self.dagPath}_tex".replace("|", "_")

    @property
    def range(self) -> str:
        try:
            return cmds.listConnections(self, type="aiRange")[0]
        except TypeError:
            return f"{self.dagPath}_rng".replace("|", "_")

    @property
    def mult(self) -> str:
        try:
            return cmds.listConnections(self, type="aiMultiply")[0]
        except TypeError:
            return f"{self.dagPath}_lineWidth".replace("|", "_")

    @property
    def noise(self) -> str:
        try:
            return cmds.listConnections(self, type="aiCellNoise")[0]
        except TypeError:
            return f"{self.dagPath}_lineNoise".replace("|", "_")

    def createShaderNetwork(self) -> None:
        # Create shadingEngine
        createNode(self.shadingGroup, "shadingEngine")
        connectAttr(f"{self}.shadingEngine", f"{self.shadingGroup}.model")

        # Create aiLambert
        createNode(self.lambert, "aiLambert")
        for source, destination in {
            f"{self.lambert}.outColor": f"{self.shadingGroup}.aiSurfaceShader",
            f"{self}.aiLambert": f"{self.lambert}.model",
        }.items():
            connectAttr(source, destination)

        # Create aiToon
        createNode(self.toon, "aiToon")
        for destination in (
            f"{self.shadingGroup}.surfaceShader",
            f"{self.lambert}.KdColor",
        ):
            connectAttr(f"{self.toon}.outColor", destination)
        connectAttr(f"{self}.aiToon", f"{self.toon}.model")

        # Create aiImage
        createNode(self.texture, "aiImage")
        for source, destination in {
            f"{self.texture}.outColor": f"{self.toon}.baseColor",
            f"{self}.aiImage": f"{self.texture}.model",
        }.items():
            connectAttr(source, destination)

        # Create aiMultiply
        createNode(self.mult, "aiMultiply")
        for source, destination in {
            f"{self.mult}.outColorR": f"{self.toon}.silhouetteWidthScale",
            f"{self}.aiMultiply": f"{self.mult}.model",
        }.items():
            connectAttr(source, destination)

        # Create aiRange
        createNode(self.range, "aiRange")
        for source, destination in {
            f"{self.range}.outColor": f"{self.mult}.input2",
            f"{self}.aiRange": f"{self.range}.model",
        }.items():
            connectAttr(source, destination)

        # Create aiCellNoise
        if not self.connectToMasterLineNoise:
            createNoiseShader(self.noise)
            for source, destination in {
                f"{self.noise}.outColor": f"{self.mult}.input1",
                f"{self}.aiCellNoise": f"{self.noise}.model",
            }.items():
                connectAttr(source, destination)

        # Apply shader network to model
        cmds.select(self.dagPath, replace=True)
        cmds.hyperShade(assign=self.shadingGroup)
        cmds.select(clear=True)

        self._assetizeNetwork()

    def _assetizeNetwork(self):
        createNode(self.asset, "container")
        cmds.setAttr(f"{self.asset}.creationDate", "2023/03", type="string")
        connectAttr(f"{self}.container", f"{self.asset}.model")

        shaders = [self.lambert, self.toon, self.texture, self.mult, self.range]
        if not self.connectToMasterLineNoise:
            shaders.append(self.noise)
        cmds.container(self.asset, edit=True, addNode=shaders, force=True)

        attributes = (
            cmds.container(self.asset, query=True, publishName=True) or []
        )
        for attribute, name in {
            f"{self.texture}.filename": "texture",
            f"{self.lambert}.opacity": "opacity",
            f"{self.toon}.normalType": "normalType",
            f"{self.toon}.angleThreshold": "angleThreshold",
            f"{self.toon}.priority": "linePriority",
            f"{self.range}.multiplier": "lineThickness",
            f"{self.toon}.edgeColor": "lineColor",
        }.items():
            if name not in attributes:
                cmds.container(
                    self.asset, edit=True, publishAndBind=(attribute, name)
                )


def connectAttr(source: str, destination: str) -> None:
    connections = cmds.listConnections(destination, source=True) or []

    if not connections:
        cmds.connectAttr(source, destination)

    elif source.split(".")[0] not in connections:
        cmds.connectAttr(source, destination, force=True)


def connectMasterShaders(model: Model, *_) -> None:
    createRampShader()

    createNode(MASTER_LINE_COLOR, "aiFlat")
    connectAttr(
        f"{MASTER_LINE_COLOR}.color", f"{MASTER_LINE_COLOR}.hardwareColor"
    )

    createNoiseShader(MASTER_LINE_NOISE)

    # Connect ramp, flat, and cellNoise to toon shaders
    model.createShaderNetwork()
    connectAttr(f"{MASTER_CEL_SHADE}.outColor", f"{model.toon}.baseTonemap")

    if model.connectToMasterLineColor:
        connectAttr(f"{MASTER_LINE_COLOR}.outColor", f"{model.toon}.edgeColor")
    else:
        try:
            cmds.disconnectAttr(
                f"{MASTER_LINE_COLOR}.outColor", f"{model.toon}.edgeColor"
            )
        except RuntimeError:
            print(
                f"{model.toon} is already disconnected from {MASTER_LINE_COLOR}."
            )

    if model.connectToMasterLineNoise:
        connectAttr(f"{MASTER_LINE_NOISE}.outColor", f"{model.mult}.input1")


def createRampShader() -> None:
    createNode(MASTER_CEL_SHADE, "aiRampRgb")
    # Set-up 5 gradients on ramp
    for i in range(5):
        color_ = i / 5 + 0.2
        for attribute, value in {
            "Interp": 0,
            "Position": i / 5,
            "Color": (color_, color_, color_),
        }.items():
            if isinstance(value, tuple):
                cmds.setAttr(
                    f"{MASTER_CEL_SHADE}.ramp[{i}].ramp_{attribute}", *value
                )
            else:
                cmds.setAttr(
                    f"{MASTER_CEL_SHADE}.ramp[{i}].ramp_{attribute}", value
                )


def createNoiseShader(name: str) -> None:
    createNode(name, "aiCellNoise")
    cmds.setAttr(f"{name}.randomness", 0.8)


def createNode(name: str, type_: str) -> None:
    if not (cmds.objExists(name) and cmds.objectType(name, isType=type_)):
        if type_ == "shadingEngine":
            cmds.sets(renderable=True, name=name, empty=True)

        if type_ == "aiLambert":
            cmds.shadingNode(type_, name=name, asUtility=True)
            cmds.setAttr(f"{name}.Kd", 1)
            connectAttr(f"{name}.KdColor", f"{name}.hardwareColor")

        elif type_ == "aiToon":
            cmds.shadingNode(type_, name=name, asShader=True)
            for attribute, value in {
                "enableSilhouette": True,
                "base": 1,
                "indirectDiffuse": 1,
            }.items():
                cmds.setAttr(f"{name}.{attribute}", value)
            for source, destination in {
                "edgeColor": "silhouetteColor",
                "baseColor": "hardwareColor",
            }.items():
                connectAttr(f"{name}.{source}", f"{name}.{destination}")

        elif type_ == "aiImage":
            cmds.shadingNode(type_, name=name, asTexture=True)
            cmds.setAttr(
                f"{name}.colorSpace", "Rec.1886 / Rec.709 video", type="string"
            )
            for attribute in ("ColorSpaceFileRules", "MissingTextures"):
                cmds.setAttr(f"{name}.ignore{attribute}", True)
            cmds.setAttr(f"{name}.missingTextureColor", 1, 1, 1, type="double3")

        elif type_ == "aiRange":
            cmds.shadingNode(type_, name=name, asUtility=True)
            cmds.setAttr(f"{name}.outputMin", 0.125)
            cmds.addAttr(
                name, longName="multiplier", min=0, max=1, defaultValue=1
            )
            connectAttr(f"{name}.multiplier", f"{name}.inputR")

        elif type_ == "aiMultiply":
            cmds.shadingNode(type_, name=name, asUtility=True)

        elif type_ in ("aiRampRgb", "aiFlat", "aiCellNoise"):
            cmds.shadingNode(type_, name=name, asRendering=True)

        elif type_ == "container":
            cmds.container(name=name)
            cmds.setAttr(f"{name}.viewMode", 0)

    if not cmds.attributeQuery("model", node=name, exists=True):
        cmds.addAttr(name, longName="model", attributeType="message")


class Window:
    NAME = "shaderManager"
    TITLE = '"A Trace" Shader Manager'

    def __init__(self) -> None:
        self._models: list[Model] = []
        self._build()
        self._update()
        cmds.showWindow(self.NAME)

    def __repr__(self) -> str:
        return self.TITLE

    def __str__(self) -> str:
        return self.NAME

    def _build(self) -> None:
        if cmds.window(self.NAME, exists=True):
            cmds.deleteUI(self.NAME, window=True)
        cmds.window(self.NAME, title=self.TITLE)

        form = cmds.formLayout("main", numberOfDivisions=100)
        self.scroll = cmds.scrollLayout(
            "scroll",
            parent=form,
            childResizable=True,
            verticalScrollBarAlwaysVisible=True,
        )
        separator1 = cmds.separator("separator1", parent=form)
        separator2 = cmds.separator("separator2", parent=form)
        helpLine = cmds.helpLine("helpLine", parent=form, height=24)

        buttons = (
            (
                add := "add_btn",
                self._add,
                "Add",
                "Add selected geometries and groups that are not already on the list.",
            ),
            (
                update := "update_btn",
                self._update,
                "Update",
                "Replace the geometries and groups on the list with the currently selected nodes.",
            ),
            (
                clear := "clear_btn",
                self._clear,
                "Clear",
                "Remove all geometries and groups from the list.",
            ),
            (
                find := "find_btn",
                self._find,
                "Find Existing Shader Networks",
                "Find all geometries and groups with existing shader networks.",
            ),
            (
                create := "create_btn",
                self._create,
                "Create Shader Networks",
                "Create shader networks for all geometries and groups on the list.",
            ),
            (
                delete := "delete_btn",
                self._delete,
                "Delete Unused Shaders",
                "Delete shaders that are not connected to geometries.",
            ),
            (
                ramp := "ramp_btn",
                self._selectMasterCel,
                "Master Cel Shade",
                "Select the master aiRampRgb shader.",
            ),
            (
                color_ := "color_btn",
                self._selectMasterColor,
                "Master Line Color",
                "Select the master aiFlat shader.",
            ),
            (
                noise := "noise_btn",
                self._selectMasterNoise,
                "Master Line Noise",
                "Select the master aiCellNoise shader.",
            ),
        )
        for id, command, label, message in buttons:
            cmds.button(
                id,
                parent=form,
                height=32,
                command=command,
                label=label,
                statusBarMessage=message,
            )
        # Arrange main window contents
        cmds.formLayout(
            form,
            edit=True,
            attachControl=(
                (find, "top", 4, add),
                (separator1, "top", 5, find),
                (self.scroll, "top", 2, separator1),
                (self.scroll, "bottom", 3, separator2),
                (separator2, "bottom", 3, create),
                (create, "bottom", 4, ramp),
                (delete, "bottom", 4, ramp),
                (ramp, "bottom", 4, helpLine),
                (color_, "bottom", 4, helpLine),
                (noise, "bottom", 4, helpLine),
            ),
            attachForm=(
                (add, "top", 7),
                (add, "left", 7),
                (update, "top", 7),
                (clear, "top", 7),
                (clear, "right", 7),
                (ramp, "left", 7),
                (noise, "right", 7),
                (find, "left", 7),
                (find, "right", 7),
                (self.scroll, "left", 5),
                (self.scroll, "right", 5),
                (create, "left", 7),
                (delete, "right", 7),
                (separator1, "left", 7),
                (separator1, "right", 7),
                (separator2, "left", 7),
                (separator2, "right", 7),
                (helpLine, "left", 7),
                (helpLine, "right", 5),
                (helpLine, "bottom", 4),
            ),
            attachPosition=(
                (add, "right", 2, 100 / 3),
                (update, "left", 2, 100 / 3),
                (update, "right", 2, 100 / 3 * 2),
                (clear, "left", 2, 100 / 3 * 2),
                (create, "right", 2, 50),
                (delete, "left", 2, 50),
                (ramp, "right", 2, 100 / 3),
                (color_, "left", 2, 100 / 3),
                (color_, "right", 2, 100 / 3 * 2),
                (noise, "left", 2, 100 / 3 * 2),
            ),
        )

    def _add(self, *_) -> None:
        selection: list[str] = cmds.ls(
            selection=True, transforms=True, long=True
        )
        selection.sort(key=lambda name: name.lower().rsplit("|", 1)[-1])
        for model in selection:
            if (model not in self._models) and cmds.listRelatives(
                model, allDescendents=True
            ):
                model = Model(model)
                model.frame = Frame(model, self.scroll, self._models)
                self._models.append(model)
        cmds.select(clear=True)

    def _clear(self, *_) -> None:
        for model in self._models:
            cmds.deleteUI(model.frame, layout=True)
        self._models.clear()

    def _update(self, *_) -> None:
        if cmds.ls(selection=True, transforms=True):
            self._clear()
            self._add()

    def _find(self, _) -> None:
        cmds.select(clear=True)
        for sg in cmds.ls(typ="shadingEngine"):
            if nodes := cmds.listConnections(sg, type="transform"):
                cmds.select(nodes, add=True)
            else:
                nodes = cmds.ls(sg.split("_sg")[0], transforms=True, long=True)
                cmds.select(nodes, add=True)
        self._add()

    def _create(self, _) -> None:
        for model in self._models:
            connectMasterShaders(model)

    def _delete(self, _) -> None:
        for sg in cmds.ls(type="shadingEngine"):
            if not cmds.listConnections(sg, type="mesh"):
                cmds.delete(sg)

        for material in cmds.ls(materials=True):
            if not cmds.listConnections(material, type="shadingEngine"):
                cmds.delete(material)

        for texture in cmds.ls(type=("aiImage", "aiMultiply", "file")):
            if not cmds.listConnections(texture, type="aiToon"):
                cmds.delete(texture)

    def _selectMasterCel(self, _) -> None:
        try:
            cmds.select(MASTER_CEL_SHADE, replace=True)
        except ValueError:
            cmds.warning("There is no existing master aiRampRgb node.")

    def _selectMasterColor(self, _) -> None:
        try:
            cmds.select(MASTER_LINE_COLOR, replace=True)
        except ValueError:
            cmds.warning("There is no existing master aiFlat node.")

    def _selectMasterNoise(self, _) -> None:
        try:
            cmds.select(MASTER_LINE_NOISE, replace=True)
        except ValueError:
            cmds.warning("There is no existing master aiCellNoise node.")


class Frame:
    def __init__(
        self, model: Model, scroll: str, modelsList: list[Model]
    ) -> None:
        self._model = model
        self._scroll = scroll
        self._modelsList = modelsList

        self._frame = cmds.frameLayout(
            f"{model.dagPath}_frame",
            parent=scroll,
            marginHeight=4,
            marginWidth=16,
            label=model.display,
            backgroundShade=True,
            collapsable=True,
            collapse=False,
        )
        form1 = cmds.formLayout(f"{model}_form1")
        controls = (
            (
                connectColor := "connectColor_cb",
                (self._uncheckLineColor, self._checkLineColor),
                "Connect to Master Line Color",
                f"If checked, connects {self._model} to the master aiFlat shader.",
            ),
            (
                connectNoise := "connectNoise_cb",
                (self._uncheckLineNoise, self._checkLineNoise),
                "Connect to Master Line Noise",
                f"If unchecked, creates a separate aiCellNoise node for {self._model}.",
            ),
            (
                select := "select_btn",
                self._select,
                "Select Shader Network",
                f"Select {self._model}'s container node.",
            ),
            (
                create := "create_btn",
                self._createShaderNetwork,
                "Create Shader Network",
                f"Create a shader network for {self._model}.",
            ),
            (
                remove := "remove_btn",
                self._remove,
                "Remove",
                f"Remove {self._model} from the list.",
            ),
        )
        for id, command, label, message in controls:
            if isinstance(command, tuple):
                cmds.checkBox(
                    id,
                    label=label,
                    offCommand=command[0],
                    onCommand=command[1],
                    statusBarMessage=message,
                    value=True,
                )
            else:
                cmds.button(
                    id, label=label, command=command, statusBarMessage=message
                )
        subframe = cmds.frameLayout(
            label="Shading Nodes",
            backgroundShade=True,
            collapsable=True,
            collapse=True,
            statusBarMessage=f"Show or hide buttons for selecting {self._model}'s individual shading nodes.",
        )
        form2 = cmds.formLayout(f"{model}_buttons_form")
        buttons = (
            (
                lambert := "lambert_btn",
                self._selectLambert,
                "Lambert",
                f"Select {self._model}'s aiLambert shader.",
            ),
            (
                toon := "toon_btn",
                self._selectToon,
                "Toon",
                f"Select {self._model}'s aiToon shader.",
            ),
            (
                image := "image_btn",
                self._selectImage,
                "Texture",
                f"Select {self._model}'s aiImage node.",
            ),
            (
                range := "range_btn",
                self._selectRange,
                "Line Range",
                f"Select {self._model}'s aiRange node.",
            ),
            (
                multiply := "multiply_btn",
                self._selectMultiply,
                "Line Multiplier",
                f"Select {self._model}'s aiMultiply node.",
            ),
            (noise := "lineNoise_btn", "", "", ""),
        )
        for id, command, label, message in buttons:
            cmds.button(
                id, label=label, command=command, statusBarMessage=message
            )

        # Arrange frame contents
        cmds.formLayout(
            form1,
            edit=True,
            attachControl=(
                (connectNoise, "top", 4, connectColor),
                (select, "left", 10, connectColor),
                (select, "bottom", 4, subframe),
                (subframe, "top", 4, connectNoise),
                (create, "top", 4, subframe),
                (remove, "top", 4, subframe),
            ),
            attachForm=(
                (connectColor, "top", 0),
                (connectColor, "left", 0),
                (connectNoise, "left", 0),
                (select, "top", 0),
                (select, "right", 0),
                (subframe, "left", 0),
                (subframe, "right", 0),
                (create, "left", 0),
                (create, "bottom", 1),
                (remove, "right", 0),
                (remove, "bottom", 1),
            ),
            attachPosition=(
                (create, "right", 2, 50),
                (remove, "left", 2, 50),
            ),
        )
        cmds.formLayout(
            form2,
            edit=True,
            attachControl=(
                (range, "top", 4, lambert),
                (multiply, "top", 4, lambert),
                (noise, "top", 4, lambert),
            ),
            attachForm=(
                (lambert, "top", 3),
                (lambert, "left", 0),
                (toon, "top", 3),
                (image, "top", 3),
                (image, "right", 0),
                (range, "left", 0),
                (range, "bottom", 0),
                (multiply, "bottom", 0),
                (noise, "right", 0),
                (noise, "bottom", 0),
            ),
            attachPosition=(
                (lambert, "right", 2, 100 / 3),
                (toon, "left", 2, 100 / 3),
                (toon, "right", 2, 100 / 3 * 2),
                (image, "left", 2, 100 / 3 * 2),
                (range, "right", 2, 100 / 3),
                (multiply, "left", 2, 100 / 3),
                (multiply, "right", 2, 100 / 3 * 2),
                (noise, "left", 2, 100 / 3 * 2),
            ),
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._model!r}, {self._scroll!r}, {self._modelsList!r})"

    def __str__(self) -> str:
        return self._frame

    def _checkLineColor(self, _) -> None:
        self._model.connectToMasterLineColor = True

    def _uncheckLineColor(self, _) -> None:
        self._model.connectToMasterLineColor = False

    def _checkLineNoise(self, _) -> None:
        self._model.connectToMasterLineNoise = True

    def _uncheckLineNoise(self, _) -> None:
        self._model.connectToMasterLineNoise = False

    def _select(self, _) -> None:
        cmds.select(self._model.asset, replace=True)

    def _selectLambert(self, _) -> None:
        try:
            cmds.select(self._model.lambert, replace=True)
        except ValueError:
            cmds.warning(
                f"There is no aiLambert shader associated with {self._model}."
            )

    def _selectToon(self, _) -> None:
        try:
            cmds.select(self._model.toon, replace=True)
        except ValueError:
            cmds.warning(
                f"There is no aiToon shader associated with {self._model}."
            )

    def _selectImage(self, _) -> None:
        try:
            cmds.select(self._model.texture, replace=True)
        except ValueError:
            cmds.warning(
                f"There is no aiImage node associated with {self._model}."
            )

    def _selectRange(self, _) -> None:
        try:
            cmds.select(self._model.range, replace=True)
        except ValueError:
            cmds.warning(
                f"There is no aiRange node associated with {self._model}."
            )

    def _selectMultiply(self, _) -> None:
        try:
            cmds.select(self._model.mult, replace=True)
        except ValueError:
            cmds.warning(
                f"There is no aiMultiply node associated with {self._model}."
            )

    def _createShaderNetwork(self, _) -> None:
        self._model.createShaderNetwork()
        connectMasterShaders(self._model)

    def _remove(self, _) -> None:
        cmds.deleteUI(self, layout=True)
        self._modelsList.remove(self._model)


if __name__ == "__main__":
    cmds.loadPlugin("mtoa", quiet=True)
    Window()
