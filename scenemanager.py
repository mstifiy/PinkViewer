import numpy as np
import vtk
from Utilities import *


class vtkPlaneCall:
    """切割vtkPlaneWidget平面回调函数"""

    def __init__(self, sceneManager, ugrid):
        self.sceneManager = sceneManager
        self.ugrid = ugrid
        self.clippingPlane = vtk.vtkPlane()  # 剖切平面

    def __call__(self, caller, ev):
        caller.GetPlane(self.clippingPlane)  # 得到当前planeWidget的平面，作为剖切平面

        clipper = vtk.vtkClipDataSet()
        clipper.SetClipFunction(self.clippingPlane)  # 设置剖切方法为平面剖切
        clipper.SetInputData(self.ugrid)  # 设置剖切对象
        # clipper.SetValue(0.0)
        clipper.GenerateClippedOutputOn()
        clipper.Update()

        insideMapper = vtk.vtkDataSetMapper()
        insideMapper.SetInputData(clipper.GetOutput())
        insideMapper.ScalarVisibilityOn()
        # clippedMapper = vtk.vtkDataSetMapper()
        # clippedMapper.SetInputData(clipper.GetClippedOutput())
        # clippedMapper.ScalarVisibilityOn()
        if clipper.GetOutput().GetPointData().GetScalars():
            scalarRange = clipper.GetOutput().GetPointData().GetScalars().GetRange()
            title = clipper.GetOutput().GetPointData().GetScalars().GetName()
            self.sceneManager.drawScalarField(insideMapper, scalarRange, title)
        else:
            self.sceneManager.drawDsSrc(clipper.GetOutput())
        self.sceneManager.ToggleVisibilityEdge(True)  # 显示边缘
        self.sceneManager.display()


class vtkSliderCall:
    """等值面显示回调函数"""

    def __init__(self, sceneManager, ugrid):
        self.sceneManager = sceneManager
        self.ugrid = ugrid
        self.value = 0  # 剖切值

    def __call__(self, caller, ev):
        self.value = caller.GetRepresentation().GetValue()

        clipper = vtk.vtkClipDataSet()
        clipper.SetInputData(self.ugrid)  # 设置剖切对象
        clipper.SetValue(self.value)
        # clipper.InsideOutOn()
        # clipper.InsideOutOff()
        clipper.GenerateClippedOutputOn()
        clipper.Update()

        insideMapper = vtk.vtkDataSetMapper()
        insideMapper.SetInputData(clipper.GetOutput())
        insideMapper.ScalarVisibilityOn()

        # clippedMapper = vtk.vtkDataSetMapper()
        # clippedMapper.SetInputData(clipper.GetClippedOutput())
        # clippedMapper.ScalarVisibilityOn()

        scalarRange = clipper.GetOutput().GetPointData().GetScalars().GetRange()
        title = clipper.GetOutput().GetPointData().GetScalars().GetName()
        self.sceneManager.drawScalarField(insideMapper, scalarRange, title)
        self.sceneManager.display()


class PointPickerInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, parent = None, dataset = None):
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
        self.dataset = dataset
        self.points = dataset.GetPoints()
        # 对拾取点进行标记
        sphereSource = vtk.vtkSphereSource()
        sphereSource.Update()
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputConnection(sphereSource.GetOutputPort())
        self.marker_actor = vtk.vtkActor()
        self.marker_actor.SetMapper(self.mapper)
        # Setup the text and add it to the renderer
        self.textActor = vtk.vtkTextActor()
        self.textActor.SetPosition(10, 10)
        self.textActor.GetTextProperty().SetFontSize(24)
        self.textActor.GetTextProperty().SetColor(241 / 255, 135 / 255, 184 / 255)
        # kd-tree
        self.tree = vtk.vtkKdTree()
        self.tree.BuildLocatorFromPoints(self.points)

    def leftButtonPressEvent(self, obj, event):
        clickPos = self.GetInteractor().GetEventPosition()
        # 打印鼠标左键像素位置
        # print(f"Picking pixel: {clickPos[0]} {clickPos[1]}")
        # 注册拾取点函数
        pointPicker = self.GetInteractor().GetPicker()
        pointPicker.Pick(clickPos[0], clickPos[1], 0, self.GetDefaultRenderer())
        # 打印拾取点空间位置
        pickId = pointPicker.GetPointId()  # 获取拾取点的ID，无ID返回-1
        if pickId != -1:
            # 显示模型上被拾取的点
            pickPos = pointPicker.GetPickPosition()
            # print(f"Picked value: {pickPos[0]} {pickPos[1]} {pickPos[2]}")
            self.GetDefaultRenderer().RemoveActor(self.marker_actor)
            self.marker_actor.SetPosition(pickPos)
            # Find the 2 closest points to pickPos
            ClosestIdList = vtk.vtkIdList()
            self.tree.FindClosestNPoints(2, pickPos, ClosestIdList)
            pt1 = self.points.GetPoint(ClosestIdList.GetId(0))
            pt2 = self.points.GetPoint(ClosestIdList.GetId(1))
            distance = np.sqrt(vtk.vtkMath.Distance2BetweenPoints(pt1, pt2))
            self.marker_actor.SetScale(distance / 4)
            self.marker_actor.GetProperty().SetColor(0.0, 1.0, 0.0)
            self.GetDefaultRenderer().AddActor(self.marker_actor)
            # 打印节点信息
            if self.dataset.GetPointData().GetScalars():
                scalars = self.dataset.GetPointData().GetScalars()
                self.textActor.SetInput("Picked Point: %.2f %.2f %.2f\nAttribute Value: %.2f" % (
                    pickPos[0], pickPos[1], pickPos[2], scalars.GetValue(pickId)))
            else:
                self.textActor.SetInput("Picked Point: %.2f %.2f %.2f\n" % (pickPos[0], pickPos[1], pickPos[2]))
            self.GetDefaultRenderer().AddActor2D(self.textActor)
        self.OnLeftButtonDown()


class CellPickerInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, parent = None):
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
        self.selectedMapper = vtk.vtkDataSetMapper()
        self.selectedActor = vtk.vtkActor()
        self.dataset = None
        # Setup the text and add it to the renderer
        self.textActor = vtk.vtkTextActor()
        self.textActor.SetPosition(10, 10)
        self.textActor.GetTextProperty().SetFontSize(24)
        self.textActor.GetTextProperty().SetColor(241 / 255, 135 / 255, 184 / 255)

    def leftButtonPressEvent(self, obj, event):
        clickPos = self.GetInteractor().GetEventPosition()
        # 打印鼠标左键像素位置
        # print(f"Picking pixel: {clickPos[0]} {clickPos[1]}")
        # 注册拾取单元函数
        cellPicker = self.GetInteractor().GetPicker()
        cellPicker.SetTolerance(0.0005)
        cellPicker.Pick(clickPos[0], clickPos[1], 0, self.GetDefaultRenderer())

        if cellPicker.GetCellId() != -1:
            # print("Pick position is: ", cellPicker.GetPickPosition())
            # print("Cell id is:", cellPicker.GetCellId())
            # print("Point id is:", cellPicker.GetPointId())
            if self.dataset is None:
                print("Source data not found! ")
                return

            cell = self.dataset.GetCell(cellPicker.GetCellId())  # 通过拾取的CellId获取vtkCell
            # 打印单元信息
            self.textActor.SetInput(f"Picked Cell Type: {cell.GetClassName()}\nCell Id: {cellPicker.GetCellId()}")
            ## 高亮选择的单元方法1
            # selectedCells = vtk.vtkUnstructuredGrid()
            # cellArray = vtk.vtkCellArray()
            # pointList = vtk.vtkPoints()
            # idList = vtk.vtkIdList()
            # points = cell.GetPoints()
            # num = points.GetNumberOfPoints()
            # p = [0.0, 0.0, 0.0]
            # for i in range(num):
            #     p = points.GetPoint(i)
            #     print(f"Point{i} :\tx = {p[0]}\ty = {p[1]}\tz ={p[2]}")
            #     idList.InsertNextId(pointList.InsertNextPoint(p))
            # selectedCells.SetPoints(pointList)
            # selectedCells.InsertNextCell(cell.GetCellType(), idList)
            # print(f"Number of points in the selection: {selectedCells.GetNumberOfPoints()}")
            # print(f"Number of cells in the selection : {selectedCells.GetNumberOfCells()}")
            # mapper = vtk.vtkDataSetMapper()
            # mapper.SetInputData(selectedCells)
            # self.GetDefaultRenderer().RemoveActor(self.selectedActor)
            # self.selectedActor.SetMapper(mapper)
            # self.selectedActor.GetProperty().EdgeVisibilityOn()
            # self.selectedActor.GetProperty().SetColor(1.0, 0.0, 0.0)
            # self.selectedActor.GetProperty().SetPointSize(5.0)
            # self.GetDefaultRenderer().AddActor(self.selectedActor)

            ## 高亮选择的单元方法2
            ids = vtk.vtkIdTypeArray()
            ids.SetNumberOfComponents(1)
            ids.InsertNextValue(cellPicker.GetCellId())

            selectionNode = vtk.vtkSelectionNode()
            selectionNode.SetFieldType(vtk.vtkSelectionNode.CELL)
            selectionNode.SetContentType(vtk.vtkSelectionNode.INDICES)
            selectionNode.SetSelectionList(ids)

            selection = vtk.vtkSelection()
            selection.AddNode(selectionNode)

            extractSelection = vtk.vtkExtractSelection()
            extractSelection.SetInputData(0, self.dataset)
            extractSelection.SetInputData(1, selection)
            extractSelection.Update()

            self.selectedMapper.SetInputData(extractSelection.GetOutput())
            self.GetDefaultRenderer().RemoveActor(self.selectedActor)
            self.selectedActor.SetMapper(self.selectedMapper)
            self.selectedActor.GetProperty().EdgeVisibilityOn()
            self.selectedActor.GetProperty().SetEdgeColor(1, 0, 0)
            self.selectedActor.GetProperty().SetLineWidth(3)
            self.GetDefaultRenderer().AddActor2D(self.textActor)
            self.GetDefaultRenderer().AddActor(self.selectedActor)
            # self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer().AddActor(self.selectedActor)

        self.OnLeftButtonDown()


class SceneManager:

    def __init__(self, vtkWidget = None):
        self.colors = vtk.vtkNamedColors()
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(1.0, 1.0, 1.0)  # 设置背景为白色
        self.window = vtkWidget.GetRenderWindow()
        self.window.AddRenderer(self.renderer)
        self.window.Render()
        self.interactor = self.window.GetInteractor()  # “演员与观众”的交互方式
        self.interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())  # 设置交互器的交互类型

        # Actor管理
        self.main_actor = None  # 主要的三维图形
        self.scalarBar_actor = vtk.vtkScalarBarActor()  # 色标带
        self.outline_actor = vtk.vtkActor()  # 包围盒
        self.silhouette_actor = vtk.vtkActor()  # 外轮廓
        self.axes_actor = vtk.vtkCubeAxesActor()  # 包围盒轴
        self.pointcloud_actor = vtk.vtkActor()  # 点云数据

        axes = vtk.vtkAxesActor()
        axes.SetShaftTypeToCylinder()
        self.orient = vtk.vtkOrientationMarkerWidget()
        self.orient.SetOrientationMarker(axes)
        self.orient.SetInteractor(self.interactor)
        self.orient.SetViewport(0.0, 0.0, 0.2, 0.2)
        self.orient.SetEnabled(1)  # Needed to set InteractiveOff
        self.orient.InteractiveOff()
        self.orient.SetEnabled(0)
        self.renderer.ResetCamera()

    def display(self):  # 显示函数
        self.renderer.ResetCamera()  # 重设渲染范围，使模型大小适应窗口
        self.window.Render()
        self.interactor.Start()

    def setBackgroundColor(self, r, g, b):  # 设置场景背景色函数
        return self.renderer.SetBackground(r, g, b)

    def drawAxes(self, length = 100.0, shaftType = 0, cylinderRadius = 0.01, coneRadius = 0.2):  # 绘制坐标轴
        axes = vtk.vtkAxesActor()
        # axes.SetShaftTypeToCylinder()
        axes.SetTotalLength(length, length, length)
        axes.SetShaftType(shaftType)
        axes.SetCylinderRadius(cylinderRadius)
        axes.SetConeRadius(coneRadius)
        axes.SetAxisLabels(0)
        self.renderer.AddActor(axes)
        return axes

    def drawActor(self, actor):  # 绘制actor对象
        self.renderer.AddActor(actor)
        return actor

    def removeActor(self, actor):  # 从场景中移除actor对象
        self.renderer.RemoveActor(actor)

    def drawPdSrc(self, pdSrc, color = (0.5, 0.5, 0.5), opacity = 1, point_size = 1):  # 绘制PolyData类型的source
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(pdSrc)
        # mapper.ScalarVisibilityOff()
        self.renderer.RemoveActor(self.main_actor)  # 移除main_actor
        self.main_actor = vtk.vtkActor()
        self.main_actor.SetMapper(mapper)
        self.main_actor.GetProperty().SetPointSize(point_size)
        self.main_actor.GetProperty().SetColor(color[0], color[1], color[2])  # 设置颜色
        self.main_actor.GetProperty().SetOpacity(opacity)  # 设置透明度
        return self.drawActor(self.main_actor)

    def drawPdSrc_2(self, pdSrc):  # 绘制PolyData类型的source
        mapper = vtk.vtkPolyDataMapper()
        if isinstance(pdSrc, vtk.vtkPolyData):
            mapper.SetInputData(pdSrc)
        else:
            mapper.SetInputConnection(pdSrc.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(2)
        return self.drawActor(actor)

    def drawDsSrc(self, DsSrc):  # 绘制DataSet类型的source
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(DsSrc)
        self.renderer.RemoveActor(self.main_actor)  # 移除main_actor
        self.main_actor = vtk.vtkActor()
        self.main_actor.SetMapper(mapper)
        self.main_actor.GetProperty().SetColor(self.colors.GetColor3d("Peacock"))  # 设置模型颜色
        return self.drawActor(self.main_actor)

    def drawPoint(self, point, radius = 2.0):  # 绘制一个点,Point3D
        src = vtk.vtkSphereSource()
        src.SetCenter(point.x, point.y, point.z)
        src.SetRadius(radius)
        return self.drawPdSrc(src)

    def drawSegment(self, seg):  # 绘制一条线段,Segment
        src = vtk.vtkLineSource()
        src.SetPoint1(seg.A.x, seg.A.y, seg.A.z)
        src.SetPoint2(seg.B.x, seg.B.y, seg.B.z)
        return self.drawPdSrc(src)

    def drawPolyline(self, _polyline):  # 绘制一条多段线, Polyline
        src = vtk.vtkLineSource()
        points = vtk.vtkPoints()
        for i in range(_polyline.count()):
            pt = _polyline.point(i)
            if hasattr(pt, 'x'):
                points.InsertNextPoint((pt.x, pt.y, pt.z))
            else:
                points.InsertNextPoint((pt[0], pt[1], pt[2]))
            src.SetPoints(points)
        return self.drawPdSrc_2(src)

    def SetViewXY(self):
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(0.0, 0.0, 3.09203)
        camera.SetViewUp(0.0, 1.0, 0.0)
        camera.SetFocalPoint(0.0, 0.0, 0.5)
        self.renderer.ResetCamera()
        self.window.Render()

    def SetViewXZ(self):
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(0.0, 3.09203, 0.5)
        camera.SetViewUp(0.0, 0.0, 1.0)
        camera.SetFocalPoint(0.0, 0.0, 0.5)
        self.renderer.ResetCamera()
        self.window.Render()

    def SetViewYZ(self):
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(3.09203, 0.0, 0.5)
        camera.SetViewUp(0.0, 0.0, 1.0)
        camera.SetFocalPoint(0.0, 0.0, 0.5)
        self.renderer.ResetCamera()
        self.window.Render()

    def Snapshot(self):
        wintoim = vtk.vtkWindowToImageFilter()
        self.window.Render()
        wintoim.SetInput(self.window)
        wintoim.Update()

        snapshot = vtk.vtkPNGWriter()
        filenamesnap = "snapshot.png"
        snapshot.SetFileName(filenamesnap)
        snapshot.SetInputConnection(0, wintoim.GetOutputPort())
        snapshot.Write()

    def ToggleVisualizeAxis(self, visible):
        self.orient.SetEnabled(1)  # Needed to set InteractiveOff
        self.orient.InteractiveOff()
        self.orient.SetEnabled(visible)
        self.window.Render()

    def ToggleVisibilityEdge(self, visible):
        if not self.main_actor:
            return
        self.main_actor.GetProperty().SetEdgeVisibility(visible)
        self.window.Render()

    def ToggleVisibility(self, visible):
        if not self.main_actor:
            return
        self.main_actor.SetVisibility(visible)
        self.window.Render()

    def ToggleOpacity(self, enable):
        if not self.main_actor:
            return
        if enable:
            self.main_actor.GetProperty().SetOpacity(0.3)  # 设置透明度
        else:
            self.main_actor.GetProperty().SetOpacity(1)  # 设置透明度
        self.window.Render()

    def ToggleOutline(self, visible):
        if not self.main_actor:
            return
        dataset = self.main_actor.GetMapper().GetInput()
        if visible:
            outline = vtk.vtkOutlineFilter()
            outline.SetInputData(dataset)
            mapOutline = vtk.vtkPolyDataMapper()
            mapOutline.SetInputConnection(outline.GetOutputPort())
            self.outline_actor.SetMapper(mapOutline)
            self.outline_actor.GetProperty().SetColor(241 / 255, 135 / 255, 184 / 255)  # 241,135,184
            self.outline_actor.GetProperty().SetLineWidth(4)
            self.renderer.AddActor(self.outline_actor)
        else:
            self.renderer.RemoveActor(self.outline_actor)
        self.window.Render()

    def ToggleSilhouette(self, visible):
        if not self.main_actor:
            return
        dataset = self.main_actor.GetMapper().GetInput()
        if visible:
            _dataset = vtk.vtkPolyData()
            if dataset.IsA('vtkPolyData'):
                _dataset.ShallowCopy(dataset)
            elif dataset.IsA('vtkUnstructuredGrid'):
                _dataset = UGrid2Pd(dataset)
            else:
                return
            silhouette = vtk.vtkPolyDataSilhouette()
            silhouette.SetCamera(self.renderer.GetActiveCamera())
            silhouette.SetInputData(_dataset)
            silhouette.SetFeatureAngle(50)
            silhouetteMapper = vtk.vtkPolyDataMapper()
            silhouetteMapper.SetInputConnection(silhouette.GetOutputPort())
            self.silhouette_actor.SetMapper(silhouetteMapper)
            self.silhouette_actor.GetProperty().SetColor(241 / 255, 135 / 255, 184 / 255)  # 241,135,184
            self.silhouette_actor.GetProperty().SetLineWidth(4)
            self.renderer.AddActor(self.silhouette_actor)
        else:
            self.renderer.RemoveActor(self.silhouette_actor)
        self.window.Render()

    def actorVisibility(self, index, visibility):
        """根据在renderer中的索引，修改一个actor的可见性"""
        props = self.renderer.GetViewProps()
        props.InitTraversal()
        for i in range(props.GetNumberOfItems()):
            if i != index:
                props.GetNextProp()
                continue
            props.GetNextProp().SetVisibility(visibility)
        self.renderer.ResetCamera()
        self.window.Render()

    def ClearAll(self):
        self.main_actor = None  # 重置main_actor
        self.renderer.RemoveAllViewProps()  # 移除所有actors
        # actors = self.renderer.GetActors()
        # actors.InitTraversal()
        # for i in range(actors.GetNumberOfItems()):
        #     self.renderer.RemoveActor(actors.GetNextProp())
        # self.renderer.ResetCamera()
        self.renderer.SetBackground(1.0, 1.0, 1.0)  # 设置背景为白色
        self.window.Render()

    def Clear3D(self, index = None):
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        if index == -1:
            self.renderer.RemoveActor(actors.GetLastProp())
        else:
            for i in range(actors.GetNumberOfItems()):
                if index is None or i == index:
                    self.renderer.RemoveActor(actors.GetNextProp())
        # self.renderer.ResetCamera()
        self.window.Render()

    def Clear2D(self, index = None):
        actors2D = self.renderer.GetActors2D()
        actors2D.InitTraversal()
        if index == -1:
            self.renderer.RemoveActor2D(actors2D.GetLastProp())
        else:
            for i in range(actors2D.GetNumberOfItems()):
                if index is None or i == index:
                    self.renderer.RemoveActor2D(actors2D.GetNextProp())
        # self.renderer.ResetCamera()
        self.window.Render()

    def showCurvaturesField(self, source):
        """计算模型曲率并显示"""
        curvaturesFilter = vtk.vtkCurvatures()
        curvaturesFilter.SetInputData(source)
        # curvaturesFilter.SetCurvatureTypeToMinimum()  # 最小曲率
        # curvaturesFilter.SetCurvatureTypeToMaximum()  # 最大曲率
        curvaturesFilter.SetCurvatureTypeToGaussian()  # 高斯曲率
        # curvaturesFilter.SetCurvatureTypeToMean()  # 平均曲率
        curvaturesFilter.Update()
        # 构建LUT
        scalarRange = curvaturesFilter.GetOutput().GetScalarRange()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(curvaturesFilter.GetOutputPort())
        title = curvaturesFilter.GetOutput().GetPointData().GetScalars().GetName()
        self.drawScalarField(mapper, scalarRange, title)
        self.display()

    def drawScalarField(self, scalar_mapper, scalarRange, title):
        # 定义颜色映射表
        lut = vtk.vtkLookupTable()
        lut.SetHueRange(0.67, 0.0)  # 色调范围从红色到蓝色
        # lut.SetAlphaRange(1.0, 1.0) # 透明度范围
        # lut.SetValueRange(1.0, 1.0)
        # lut.SetSaturationRange(1.0, 1.0) # 颜色饱和度
        # lut.SetNumberOfTableValues(256)
        lut.SetNumberOfColors(256)  # 颜色个数
        # lut.SetRange(scalarRange)
        lut.Build()

        # color_scheme = 0
        # MakeLUT(color_scheme, lut)

        scalar_mapper.SetScalarRange(scalarRange)
        scalar_mapper.SetLookupTable(lut)
        self.renderer.RemoveActor(self.main_actor)  # 移除main_actor
        self.main_actor = vtk.vtkActor()
        self.main_actor.SetMapper(scalar_mapper)
        self.main_actor.GetProperty().SetPointSize(3)
        self.main_actor.GetProperty().SetOpacity(1)  # 设置透明度
        # self.main_actor.GetProperty().SetColor(241 / 255, 135 / 255, 184 / 255)  # 设置颜色
        self.renderer.AddActor(self.main_actor)
        # 色标带
        self.scalarBar_actor.SetLookupTable(scalar_mapper.GetLookupTable())  # 将颜色查找表传入窗口中的色标带
        self.scalarBar_actor.SetTitle(title)
        self.scalarBar_actor.SetNumberOfLabels(5)
        self.renderer.AddActor2D(self.scalarBar_actor)

    def clipFEModel_plane(self, ugrid, origina = (0, 0, 0), normal = (0, 1, 1)):

        bounds = ugrid.GetBounds()
        center = ugrid.GetCenter()

        self.ClearAll()

        # 构造剖切平面
        origina = ugrid.GetCenter()
        clipPlane = vtk.vtkPlane()
        clipPlane.SetOrigin(origina)  # 设置平面原点
        clipPlane.SetNormal(normal)  # 设置平面法向

        # clipper = vtk.vtkTableBasedClipDataSet()
        clipper = vtk.vtkClipDataSet()
        clipper.SetClipFunction(clipPlane)  # 设置剖切方法为平面剖切
        clipper.SetInputData(ugrid)  # 设置剖切对象
        # clipper.SetValue(0.0)
        clipper.GenerateClippedOutputOn()
        clipper.Update()

        insideMapper = vtk.vtkDataSetMapper()
        insideMapper.SetInputData(clipper.GetOutput())
        insideMapper.ScalarVisibilityOn()

        # insideActor = vtk.vtkActor()
        # insideActor.SetMapper(insideMapper)
        # insideActor.GetProperty().SetDiffuseColor(self.colors.GetColor3d("banana"))
        # insideActor.GetProperty().SetAmbient(.3)
        # insideActor.GetProperty().EdgeVisibilityOn()

        # clippedMapper = vtk.vtkDataSetMapper()
        # clippedMapper.SetInputData(clipper.GetClippedOutput())
        # clippedMapper.ScalarVisibilityOn()

        scalarRange = clipper.GetOutput().GetPointData().GetScalars().GetRange()
        title = clipper.GetOutput().GetPointData().GetScalars().GetName()
        self.drawScalarField(insideMapper, scalarRange, title)
        self.display()

        # clippedActor = vtk.vtkActor()
        # clippedActor.SetMapper(clippedMapper)
        # # clippedActor.GetProperty().SetDiffuseColor(self.colors.GetColor3d("tomato"))
        # # insideActor.GetProperty().SetAmbient(.3)
        # clippedActor.GetProperty().EdgeVisibilityOn()
        #
        # self.renderer.AddViewProp(clippedActor)
        # # self.renderer.AddViewProp(actor)
        # # self.renderer.AddViewProp(insideActor)
        #
        # self.renderer.ResetCamera()
        # self.renderer.GetActiveCamera().Dolly(1.4)
        # self.renderer.ResetCameraClippingRange()
        # self.window.Render()
        # self.interactor.Start()

    def clipFEModel_planeWidget(self, ugrid):
        self.ToggleSilhouette(True)  # 显示外轮廓
        self.ToggleVisibilityEdge(True)  # 显示边缘
        # 三维切割平面控件构建
        self.planeWidget = vtk.vtkPlaneWidget()
        self.planeWidget.SetInteractor(self.interactor)  # 与交互器关联
        self.planeWidget.SetInputData(ugrid)  # 设置数据集，用于初始化平面，可以不设置
        self.planeWidget.SetResolution(1)  # 即：设置网格数
        self.planeWidget.GetPlaneProperty().SetColor(.2, .8, 0.1)  # 设置颜色
        self.planeWidget.GetPlaneProperty().SetOpacity(1)  # 设置透明度
        self.planeWidget.GetPlaneProperty().SetLineWidth(4)
        self.planeWidget.GetHandleProperty().SetColor(0, .4, .7)  # 设置平面顶点颜色
        self.planeWidget.GetHandleProperty().SetPointSize(1)
        self.planeWidget.GetHandleProperty().SetLineWidth(1)  # 设置平面线宽
        self.planeWidget.NormalToZAxisOn()  # 初始法线方向平行于Z轴
        self.planeWidget.SetRepresentationToWireframe()  # 平面显示为网格属性 SetRepresentationToSurface()
        self.planeWidget.SetCenter(ugrid.GetCenter())  # 设置平面坐标
        self.planeWidget.SetPlaceFactor(1.0)
        self.planeWidget.PlaceWidget()  # 放置平面
        self.planeWidget.On()  # 显示平面
        #  设置vtkPlaneCallback
        self.planeWidget.AddObserver(vtk.vtkCommand.InteractionEvent, vtkPlaneCall(self, ugrid))

    def isosurface_extraction(self, ugrid):

        # 实例化vtkSliderRepresentation3D，并设置属性。该对象用做滑块在场景中的3D表示
        sliderRep = vtk.vtkSliderRepresentation3D()
        # 滑动条两端的值，默认0 - 100
        valueRange = ugrid.GetPointData().GetScalars().GetRange()
        sliderRep.SetMinimumValue(valueRange[0])
        sliderRep.SetMaximumValue(valueRange[1])
        # sliderRep.SetValue(valueRange[0])  # 设置滑动条滑块的初始值
        sliderRep.SetTitleText("Isosurface Value")  # 标题文本
        # 文本位置
        sliderRep.GetPoint1Coordinate().SetCoordinateSystemToWorld()
        sliderRep.GetPoint1Coordinate().SetValue(-100, 0, 0)
        sliderRep.GetPoint2Coordinate().SetCoordinateSystemToWorld()
        sliderRep.GetPoint2Coordinate().SetValue(100, 0, 0)  # Titletext的坐标
        # 相关尺寸
        sliderRep.SetSliderLength(0.08)
        sliderRep.SetSliderWidth(0.08)
        sliderRep.SetEndCapLength(0.05)

        self.sliderWidget = vtk.vtkSliderWidget()
        self.sliderWidget.SetInteractor(self.interactor)
        self.sliderWidget.SetRepresentation(sliderRep)
        self.sliderWidget.SetAnimationModeToAnimate()
        self.sliderWidget.EnabledOn()
        self.sliderWidget.AddObserver(vtk.vtkCommand.InteractionEvent, vtkSliderCall(self, ugrid))

    def drawVectorField(self, FEMapper, sample_ratio = 10, scale_ratio = 0.015, symbol = 'arrow'):
        self.renderer.RemoveActor(self.main_actor)
        self.main_actor = vtk.vtkActor()
        self.main_actor.SetMapper(FEMapper)
        self.ToggleOpacity(True)
        self.main_actor.GetProperty().SetColor(241 / 255, 135 / 255, 184 / 255)  # 设置颜色
        # 数据采样
        maskPoints = vtk.vtkMaskPoints()
        maskPoints.SetInputData(FEMapper.GetInput())
        maskPoints.SetOnRatio(sample_ratio)  # 采样率
        maskPoints.Update()
        # 符号化向量场
        glyph3D = vtk.vtkGlyph3D()  # vtkGlyph3D是一个过滤器，他会将固定的几何数据（符号数据）复制到输入的数据集的每一个点上
        glyph3D.SetInputData(maskPoints.GetOutput())
        if symbol == 'arrow':
            arrow = vtk.vtkArrowSource()  # 箭头符号
            arrow.Update()
            glyph3D.SetSourceData(arrow.GetOutput())  # 设置符号
        elif symbol == 'cone':
            cone = vtk.vtkConeSource()  # 圆锥符号
            cone.SetResolution(6)  # 设置用于表示圆锥的面数
            cone.Update()
            glyph3D.SetSourceData(cone.GetOutput())  # 设置符号
        # glyph3D.SetVectorModeToUseNormal()  # 使用法向控制符号方向
        glyph3D.SetVectorModeToUseVector()  # 使用向量控制符号方向
        glyph3D.SetScaleModeToScaleByVector()  # 使用点上的vector数据控制缩放
        # glyph3D.SetScaleModeToDataScalingOff()  # 这里没有标量，所以关闭符号缩放控制
        glyph3D.SetScaleFactor(scale_ratio)  # 设置缩放比例
        glyph3D.Update()

        glMapper = vtk.vtkDataSetMapper()
        glMapper.SetInputData(glyph3D.GetOutput())
        glMapper.Update()
        glActor = vtk.vtkActor()
        glActor.SetMapper(glMapper)
        glActor.GetProperty().SetColor(0.0, 0.79, 0.34)  # glyphActor

        self.renderer.AddActor(self.main_actor)
        self.renderer.AddActor(glActor)

    def piontPick(self):
        if not self.main_actor:
            return
        dataset = self.main_actor.GetMapper().GetInput()

        pointPicker = vtk.vtkPointPicker()
        self.interactor.SetPicker(pointPicker)  # 设置pointPicker
        style = PointPickerInteractorStyle(dataset = dataset)  # 设置自定义的点拾取交互类型
        style.SetDefaultRenderer(self.renderer)
        self.interactor.SetInteractorStyle(style)

    def cellPick(self):
        if not self.main_actor:
            return
        self.ToggleOpacity(True)  # 透明显示，以便单元观察
        cellPicker = vtk.vtkCellPicker()
        self.interactor.SetPicker(cellPicker)  # 设置cellPicker
        style = CellPickerInteractorStyle()  # 设置自定义的单元拾取交互类型
        style.dataset = self.main_actor.GetMapper().GetInput()
        style.SetDefaultRenderer(self.renderer)
        self.interactor.SetInteractorStyle(style)

    def meshSimplify(self, ratio):
        if not self.main_actor:
            return None
        original = self.main_actor.GetMapper().GetInput()
        if not original.IsA('vtkPolyData'):
            return None
        # print(f"简化前-----------------------\n模型点数为： {original.GetNumberOfPoints()}\n模型面数为： {original.GetNumberOfPolys()}")
        # 模型抽取操作
        # decimation = vtk.vtkDecimatePro()
        decimation = vtk.vtkQuadricDecimation()
        # decimation = vtk.vtkQuadricClustering()
        decimation.SetInputData(original)
        try:
            decimation.SetTargetReduction(ratio)  # 简化率，代表百分之ratio的三角面片单元将被移除
        except AttributeError:
            decimation.UseFeatureEdgesOn()  # 此时用vtkQuadricClustering
        decimation.Update()

        decimated = decimation.GetOutput()
        # print(f"简化后-----------------------\n模型点数为： {decimated.GetNumberOfPoints()}\n模型面数为： {decimated.GetNumberOfPolys()}")
        self.drawPdSrc(decimated)
        self.ToggleVisibilityEdge(True)
        self.display()
        return decimated

    def meshRefine(self, sub_num):
        if not self.main_actor:
            return None
        original = self.main_actor.GetMapper().GetInput()
        if not original.IsA('vtkPolyData'):
            return None
        print(
            f"细化前-----------------------\n模型点数为： {original.GetNumberOfPoints()}\n模型面数为： {original.GetNumberOfPolys()}")
        # 模型细化操作
        subdivision = vtk.vtkLinearSubdivisionFilter()  # 线性网格细分滤波器
        # subdivision = vtk.vtkLoopSubdivisionFilter()  # Loop网格细分滤波器
        # subdivision = vtk.vtkButterflySubdivisionFilter()  # butterfly网格细分滤波器
        subdivision.SetInputData(original)
        subdivision.SetNumberOfSubdivisions(sub_num)
        subdivision.Update()

        refined = subdivision.GetOutput()
        print(f"细化后-----------------------\n模型点数为： {refined.GetNumberOfPoints()}\n模型面数为： {refined.GetNumberOfPolys()}")
        self.drawPdSrc(refined)
        self.ToggleVisibilityEdge(True)
        self.display()
        return refined

    def drawPointCloud(self, pointsCloud):
        """绘制点云"""
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(pointsCloud)
        self.renderer.RemoveActor(self.main_actor)  # 移除main_actor
        self.main_actor = vtk.vtkActor()
        self.main_actor.SetMapper(mapper)
        self.main_actor.GetProperty().SetPointSize(3)
        self.main_actor.GetProperty().SetColor(241 / 255, 135 / 255, 184 / 255)  # 设置颜色
        self.main_actor.GetProperty().SetOpacity(1)  # 设置透明度
        return self.drawActor(self.main_actor)
