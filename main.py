import os
import sys

import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore, Qt
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtCore import QRect
from UI_MainWindow import Ui_MainWindow
from Utilities import *
from scenemanager import SceneManager

__version__ = '1.0'
__author__ = 'mstifiy'
__appname__ = 'PinkVeiwer'


class PinkViwerMainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, parent = None):
        super(PinkViwerMainWindow, self).__init__(parent)
        self.setupUi(self)
        # TODO: 可接受拖放文件
        self.setAcceptDrops(True)  # 设置接受拖拽
        self.load_settings()
        self.init_vtk_view()
        self.original_model = None
        self.pointCloud = None
        self.setWindowTitle('{} - v{}'.format(__appname__, __version__))
        self.setWindowIcon(QtGui.QIcon('images/app_logo.png'))

    def file_open(self):
        self.filename, _type = QtWidgets.QFileDialog.getOpenFileName(self, '打开文件', self.last_path,
                                                                     '*.vtk;;*.stl;;*.xyz;;*.*')
        if self.filename:
            self.setting.setValue('LastFilePath', os.path.dirname(self.filename))  # 保存当前目录的路径到配置文件中
            # 绘制图形
            self.SceneManager.ClearAll()
            if _type == '*.xyz':  # 点云绘制
                self.original_model = read_xyz(self.filename)
                self.SceneManager.drawPdSrc(self.original_model, (241 / 255, 135 / 255, 184 / 255), point_size = 3)
            elif _type == '.inp':
                self.FEModel = FEDataModel()
                self.FEModel.read_inp(self.filename)
                self.SceneManager.drawDsSrc(self.FEModel.ugrid)
            else:
                self.original_model = ReadPolyData(self.filename).GetOutput()
                self.SceneManager.drawPdSrc(self.original_model)
            self.SceneManager.display()

    def folder_open(self):
        self.files_list = []  # 文件列表
        # 选择文件夹
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self, '打开文件夹', self.last_path)
        if dir_path:
            self.last_path = dir_path
            self.setting.setValue('LastFilePath', self.last_path)  # 保存当前目录的路径到配置文件中
            # 读取文件夹文件
            self.files_list.clear()
            # 去除子文件夹名 TODO: 判断方法有待优化
            self.files_list = [i for i in os.listdir(dir_path) if '.' in i]
            self.fileTreeModel.updataData(self.files_list)

    def side_button_clicked(self):
        bt_y = int(self.file_treeView.height() / 2 - self.side_button.height() / 2)
        bt_w, bt_h = self.side_button.width(), self.side_button.height()
        fw_x, fw_y = 20, 0
        # 显示侧边栏
        if not self.m_bSideflag:
            self.m_propertyAnimation.setStartValue(
                QRect(fw_x, fw_y, self.file_treeView.width(), self.file_treeView.height()))
            self.m_propertyAnimation.setEndValue(
                QRect(fw_x + self.file_treeView.width(), fw_y, self.file_treeView.width(), self.file_treeView.height()))
            self.m_propertyAnimation.start()

            self.m_propertyAnimation2.setStartValue(QRect(0, bt_y, bt_w, bt_h))
            self.m_propertyAnimation2.setEndValue(QRect(self.file_treeView.width(), bt_y, bt_w, bt_h))
            self.m_propertyAnimation2.start()

            self.side_button.setIcon(self.left_icon)
            self.m_bSideflag = not self.m_bSideflag
        else:
            self.m_propertyAnimation.setStartValue(
                QRect(fw_x + self.file_treeView.width(), fw_y, self.file_treeView.width(), self.file_treeView.height()))
            self.m_propertyAnimation.setEndValue(
                QRect(fw_x, fw_y, self.file_treeView.width(), self.file_treeView.height()))
            self.m_propertyAnimation.start()

            self.m_propertyAnimation2.setStartValue(QRect(self.file_treeView.width(), bt_y, bt_w, bt_h))
            self.m_propertyAnimation2.setEndValue(QRect(0, bt_y, bt_w, bt_h))
            self.m_propertyAnimation2.start()

            self.side_button.setIcon(self.right_icon)
            self.m_bSideflag = not self.m_bSideflag

    def fit_all(self):
        self.SceneManager.renderer.ResetCamera()
        self.SceneManager.window.Render()

    def SetViewXY(self):
        # Ensure UI is sync (if view was selected from menu)
        self.radioButtonXY.setChecked(True)
        self.SceneManager.SetViewXY()

    def SetViewXZ(self):
        # Ensure UI is sync (if view was selected from menu)
        self.radioButtonXZ.setChecked(True)
        self.SceneManager.SetViewXZ()

    def SetViewYZ(self):
        # Ensure UI is sync (if view was selected from menu)
        self.radioButtonYZ.setChecked(True)
        self.SceneManager.SetViewYZ()

    def Snapshot(self):
        self.SceneManager.Snapshot()
        self.statusbar.showMessage("take a snapshot sucessfully", 3000)

    def ToggleVisualizeAxis(self, visible):
        # Ensure UI is sync
        self.visualize_axis_action.setChecked(visible)
        self.checkVisualizeAxis.setChecked(visible)
        self.SceneManager.ToggleVisualizeAxis(visible)

    def ToggleVisibilityEdge(self, visible):
        self.visibilityEdge_action.setChecked(visible)
        # self.checkVisibilityEdge.setChecked(visible)
        self.SceneManager.ToggleVisibilityEdge(visible)

    def ToggleVisibility(self, visible):
        # Ensure UI is sync
        self.visibility_action.setChecked(visible)
        self.checkVisibility.setChecked(visible)
        self.SceneManager.ToggleVisibility(visible)

    def ToggleOpacity(self, enable):
        self.SceneManager.ToggleOpacity(enable)

    def ToggleOutline(self, visible):
        self.SceneManager.ToggleOutline(visible)

    def ToggleSilhouette(self, visible):
        self.SceneManager.ToggleSilhouette(visible)

    def ClearAll(self):
        self.SceneManager.ClearAll()
        self.FEModel = FEDataModel()
        self.original_model = None

    def help(self):
        pass

    def about(self):
        QtWidgets.QMessageBox.about(self, self.tr('关于PinkCAx'),
                                    """<b>PinkCAx</b> v{} by {}""".format(__version__, __author__))

    def init_vtk_view(self):
        # self.show()  # We need to call QVTKWidget's show function before initializing the interactor
        self.SceneManager = SceneManager(self.vtk_widget)

    def closeEvent(self, event):
        self.setting = QtCore.QSettings("config/config.ini", QtCore.QSettings.IniFormat)
        self.setting.setValue('MainWindow/Geometry', QtCore.QVariant(self.saveGeometry()))
        self.setting.setValue('MainWindow/State', QtCore.QVariant(self.saveState()))

    def load_settings(self):
        # 使用QSettings恢复上次关闭时的状态，主要为窗口位置和大小
        self.setting = QtCore.QSettings("config/config.ini", QtCore.QSettings.IniFormat)
        self.setting.setIniCodec('UTF-8')  # 设置UTF8编码，反正保存配置文件时出现乱码
        self.restoreGeometry(self.setting.value('MainWindow/Geometry', type = QtCore.QByteArray))
        self.restoreState(self.setting.value('MainWindow/State', type = QtCore.QByteArray))
        # 读取上一次的目录路径
        self.last_path = self.setting.value('LastFilePath')
        if self.last_path is None:  # 如果字符串为空，将路径索引到根目录
            self.last_path = '.'  # 当前目录

    def draw_displacement(self):
        # 已经打开结果文件才执行
        if hasattr(self, "filename"):
            show_displacement = self.deformation_check_box.isChecked()
            # 如果显示变形，则隐藏原始模型
            if show_displacement:
                self.SceneManager.actorVisibility(0, False)
                # 模态结果跟静力学结果不同，目前的后处理仅仅是针对静力学结果
                # 只能先显示某一阶模态，这里取一阶模态进行显示
                # 以后改进
                if not hasattr(self, "deformation_actor"):
                    self.original_model.SetVectorsName('mode1')
                    self.normals = vtk.vtkPolyDataNormals()
                    self.normals.SetInputData(self.original_model)
                    # 滤波器vtkWarpVector：通过在点向量的方向上进行缩放来修改点坐标
                    self.warp = vtk.vtkWarpVector()
                    self.warp.SetInputConnection(self.normals.GetOutputPort())

                    deformation_mapper = vtk.vtkDataSetMapper()
                    deformation_mapper.SetInputConnection(self.warp.GetOutputPort())
                    self.deformation_actor = vtk.vtkActor()
                    self.deformation_actor.SetMapper(deformation_mapper)
                    self.deformation_actor.GetProperty().SetColor(0.5, 0.5, 0.5)

                    self.SceneManager.renderer.AddActor(self.deformation_actor)

                factor = self.deformation_scale_spinbox.value()
                self.warp.SetScaleFactor(factor)

                if self.deformation_combo_box.currentText() == '仅显示变形':
                    if hasattr(self, "outline_actor"):
                        self.outline_actor.VisibilityOff()
                    self.deformation_actor.VisibilityOn()
                elif self.deformation_combo_box.currentText() == '初始轮廓+变形':
                    if hasattr(self, "outline_actor"):
                        self.outline_actor.VisibilityOn()
                        self.deformation_actor.VisibilityOn()
                    else:
                        outline = vtk.vtkOutlineFilter()
                        outline.SetInputData(self.original_model)

                        outline_mapper = vtk.vtkPolyDataMapper()
                        outline_mapper.SetInputConnection(outline.GetOutputPort())
                        self.outline_actor = vtk.vtkActor()
                        self.outline_actor.SetMapper(outline_mapper)
                        self.outline_actor.GetProperty().SetColor(1.0, 0.5, 0.5)

                        self.SceneManager.renderer.AddActor(self.outline_actor)
            # 不显示变形时，隐藏原始轮廓、隐藏变形，显示原始模型
            else:
                if hasattr(self, "deformation_actor"):
                    self.deformation_actor.VisibilityOff()
                if hasattr(self, "outline_actor"):
                    self.outline_actor.VisibilityOff()
                self.SceneManager.actorVisibility(0, True)
            self.SceneManager.window.Render()

    def draw_contour(self):
        pass

    def show_curvatures_field(self):
        if self.original_model:
            self.SceneManager.showCurvaturesField(self.original_model)

    def load_INP_file(self):
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(self, '加载inp文件', self.last_path, '*.inp')
        if fn:
            self.FEModel = FEDataModel()
            self.FEModel.read_inp(fn)
            # 绘制图形
            self.SceneManager.ClearAll()
            self.SceneManager.drawDsSrc(self.FEModel.ugrid)
            self.SceneManager.display()

    def load_NTL_file(self):
        if not hasattr(self, 'FEModel'):
            self.statusbar.showMessage("请先加载INP文件！", 5000)
            return
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(self, '加载ntl文件', self.last_path, '*.ntl')
        if fn:
            self.FEModel.read_ntl(fn)
            self.SceneManager.ClearAll()
            mapper = vtk.vtkDataSetMapper()
            mapper.SetInputData(self.FEModel.ugrid)
            scalarRange = self.FEModel.ugrid.GetPointData().GetScalars().GetRange()
            title = self.FEModel.ugrid.GetPointData().GetScalars().GetName()
            self.SceneManager.drawScalarField(mapper, scalarRange, title)
            self.SceneManager.display()

    def save_mesh(self):
        if not hasattr(self, 'original_model'):
            self.statusbar.showMessage("请先加载网格模型！", 3000)
            return
        save_fn, _ = QtWidgets.QFileDialog.getSaveFileName(self, "保存当前模型", self.last_path,
                                                           "VTK文件(*.vtk)\nSTL文件(*.stl)")
        if save_fn:
            writer = WritePolyData(save_fn)
            writer.SetInputData(self.original_model)
            writer.Write()
            writer.Update()
            self.statusbar.showMessage("Save to " + save_fn + " sucessfully!", 3000)

    def save_femodel(self):
        if not hasattr(self, 'FEModel'):
            self.statusbar.showMessage("请先加载有限元模型！", 3000)
            return
        save_fn, _ = QtWidgets.QFileDialog.getSaveFileName(self, "保存当前有限元模型", self.last_path,
                                                           "VTK文件(*.vtk)")
        writer = vtk.vtkUnstructuredGridWriter()
        writer.SetFileName(save_fn)
        writer.SetInputData(self.FEModel.ugrid)
        writer.Write()
        writer.Update()
        self.statusbar.showMessage("Save to " + save_fn + " sucessfully!", 3000)

    def load_vtkFEModel(self):
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(self, '加载vtk有限元模型', self.last_path, '*.vtk')
        if fn:
            reader = vtk.vtkUnstructuredGridReader()
            reader.SetFileName(fn)
            reader.Update()
            self.FEModel.ugrid = reader.GetOutput()
            mapper = vtk.vtkDataSetMapper()
            mapper.SetInputData(reader.GetOutput())
            if reader.GetOutput().GetPointData().GetScalars():  # 标量场绘制
                scalarRange = reader.GetOutput().GetPointData().GetScalars().GetRange()
                title = reader.GetOutput().GetPointData().GetScalars().GetName()
                self.SceneManager.drawScalarField(mapper, scalarRange, title)
                self.SceneManager.display()
            elif reader.GetOutput().GetPointData().GetVectors():  # 向量场绘制
                self.SceneManager.drawVectorField(mapper)
                self.SceneManager.display()
            else:
                return

    def clip_view(self):
        if self.FEModel.ugrid.GetNumberOfPoints() != 0:
            self.SceneManager.clipFEModel_planeWidget(self.FEModel.ugrid)
            self.SceneManager.display()
        elif self.original_model.GetNumberOfPoints() != 0:
            self.SceneManager.clipFEModel_planeWidget(self.original_model)
            self.SceneManager.display()

    def isosurface_extraction(self):
        if self.FEModel.ugrid.GetNumberOfPoints() != 0:
            self.SceneManager.isosurface_extraction(self.FEModel.ugrid)
            self.SceneManager.display()

    def ToggleVisibilityBB(self, visibility):
        axes = self.SceneManager.axes_actor
        if visibility:
            # 创建三维坐标轴
            if not self.SceneManager.main_actor:
                return
            axes.SetBounds(self.SceneManager.main_actor.GetMapper().GetInput().GetBounds())
            axes.SetCamera(self.SceneManager.renderer.GetActiveCamera())  # 设置相机，以执行缩放
            ## 轴的设置
            # axes.SetXAxisRange(0, 200000)  # 设置x、y、z轴的起始和终止值
            # axes.SetYAxisRange(0, 200000)
            # axes.SetZAxisRange(0, 200000)
            axes.GetXAxesLinesProperty().SetLineWidth(1.)  # 设置坐标轴线的宽度，默认为1.0
            axes.GetYAxesLinesProperty().SetLineWidth(1.)
            axes.GetZAxesLinesProperty().SetLineWidth(1.)
            axes.SetScreenSize(10)  # 设置标题和标签文本的大小，默认值为10.0
            axes.SetLabelOffset(5)  # 指定标签与轴之间的距离，默认值为20.0
            axes.SetVisibility(True)  # 显示坐标轴
            axes.SetFlyMode(0)  # 指定一种模式来控制轴的绘制方式，0外边缘,1最近位置,2最远位置,3静态最近位置，不随摄像头动而跳变位置,4静态所有外边缘位置，不随摄像头动而跳变位置。
            # axes.SetInertia(1)# 设置惯性因子，该惯性因子控制轴切换位置的频率（从一个轴跳到另一个轴）
            # for i in range(3):  # 设置轴标签和轴标题文本样式
            #     axes.GetLabelTextProperty(i).SetColor(241 / 255, 135 / 255, 184 / 255)
            #     axes.GetTitleTextProperty(i).SetColor(241 / 255, 135 / 255, 184 / 255)
            ## 网格设置
            axes.DrawXGridlinesOn()  # 开启x、y、z轴的网格线绘制
            axes.DrawYGridlinesOn()
            axes.DrawZGridlinesOn()
            axes.SetDrawXInnerGridlines(False)  # 设置x、y、z轴的内部网格线不绘制
            axes.SetDrawYInnerGridlines(False)
            axes.SetDrawZInnerGridlines(False)
            # axes.GetXAxesGridlinesProperty().SetColor(241 / 255, 135 / 255, 184 / 255)  # 设置x、y、z轴网格线的颜色
            # axes.GetYAxesGridlinesProperty().SetColor(241 / 255, 135 / 255, 184 / 255)
            # axes.GetZAxesGridlinesProperty().SetColor(241 / 255, 135 / 255, 184 / 255)
            axes.SetGridLineLocation(2)  # 指定网格线呈现的样式，0：呈现所有网格线；1：呈现最近的三个轴的网格线；2：呈现最远的三个轴的网格线
            ## 刻度的设置
            axes.XAxisMinorTickVisibilityOff()  # 不显示x、y、z轴的次刻度
            axes.YAxisMinorTickVisibilityOff()
            axes.ZAxisMinorTickVisibilityOff()
            axes.SetLabelScaling(False, 0, 0, 0)  # 设置刻度标签的显示方式(参数1为false，刻度标签按0-200000显示；为true时，按0-200显示)
            axes.SetTickLocation(1)  # 设置刻度线显示的位置(0内部、1外部、2两侧)

            self.SceneManager.renderer.AddViewProp(axes)
            self.SceneManager.renderer.SetBackground(241 / 255, 135 / 255, 184 / 255)
        else:
            self.SceneManager.renderer.RemoveActor(axes)
            self.SceneManager.renderer.SetBackground(1, 1, 1)
        self.SceneManager.display()

    def loadScalarField(self):
        if not self.SceneManager.main_actor:
            return
        fn, _type = QtWidgets.QFileDialog.getOpenFileName(self, '打开标量场文件', self.last_path, '*.csv;;*.ntl')
        if fn:
            if _type == "*.ntl":
                scalars = self.FEModel.read_ntl(fn)
            elif _type == '*.csv':
                scalars = self.FEModel.read_csv(fn)
            self.setting.setValue('LastFilePath', os.path.dirname(fn))  # 保存当前目录的路径到配置文件中
            # 标量场绘制
            mapper = self.SceneManager.main_actor.GetMapper()
            mapper.GetInput().GetPointData().SetScalars(scalars)
            scalarRange = self.FEModel.ugrid.GetPointData().GetScalars().GetRange()
            title = self.FEModel.ugrid.GetPointData().GetScalars().GetName()
            self.SceneManager.drawScalarField(mapper, scalarRange, title)
            self.SceneManager.display()

    def calDifference(self):
        # 选择多个属性文件
        fns, filetype = QtWidgets.QFileDialog.getOpenFileNames(self, "属性文件(s)选择", self.last_path, "Text Files (*.csv)")
        if len(fns) != 2:
            self.statusbar.showMessage("请选择两个文件！", 3000)
            return
        attr1 = np.loadtxt(fns[0], delimiter = ",")
        attr2 = np.loadtxt(fns[1], delimiter = ",")
        if len(attr1) != len(attr2):
            self.statusbar.showMessage("属性数据数量不同，无法计算！", 3000)
            return
        attr_diff = np.abs(attr1 - attr2)  # 计算数据误差
        diff_max, diff_min, diff_mean = np.max(attr_diff), np.min(attr_diff), np.mean(attr_diff)
        result_txt = f'最大差值：{diff_max}\n最小差值：{diff_min}\n平均差值：{diff_mean}\n'
        # 窗口显示计算结果
        reply = QMessageBox.information(self, '计算结果', result_txt + '是否保存结果？', QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.No)
        if reply == QMessageBox.Yes:
            np.savetxt("diff_result.csv", attr_diff, delimiter = ',')
            self.statusbar.showMessage("计算结果文件保存至" + os.getcwd() + "\diff_result.csv", 3000)

    def cast_step_predict(self):
        """根据铸造步数预测属性值"""
        # 显示步数
        step = self.step_slider.value()
        self.step_control_label.setText('Step: ' + str(step))
        # 根据步数进行铸件属性预测
        if not self.PModel or len(self.PModel.model) == 0 or len(self.FEModel.nodes) == 0:
            self.statusbar.showMessage('请先进行代理模型配置！', 3000)
            return
        pre_attr = self.PModel.predict_step(step)
        # 标量场绘制
        self.FEModel.setScalar(pre_attr)
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(self.FEModel.ugrid)
        scalarRange = self.FEModel.ugrid.GetPointData().GetScalars().GetRange()
        title = self.FEModel.ugrid.GetPointData().GetScalars().GetName()
        self.SceneManager.ClearAll()
        self.SceneManager.drawScalarField(mapper, scalarRange, title)
        self.SceneManager.display()

    def mesh2points(self):
        """网格转点云"""
        points = vtk.vtkPolyData()
        if self.original_model:
            points.SetPoints(self.original_model.GetPoints())
        elif len(self.FEModel.nodes) != 0:
            points.SetPoints(self.FEModel.ugrid.GetPoints())

        # vtkVertexGlyphFilter类将丢弃输入数据中的所有单元，取而代之的是在每个点上创建一个顶点
        vertexGlyphFilter = vtk.vtkVertexGlyphFilter()
        vertexGlyphFilter.AddInputData(points)
        vertexGlyphFilter.Update()
        self.pointCloud = vertexGlyphFilter.GetOutput()
        self.SceneManager.drawPdSrc(self.pointCloud, (241 / 255, 135 / 255, 184 / 255), point_size = 3)
        self.SceneManager.display()

    def samplingPoints(self, tolerance):
        tolerance = 0.01
        # vtkCleanPolyData是一个过滤器，它将多边形数据作为输入并生成多边形数据作为输出。
        # 作用为合并重复点（可通过指定tolerance实现采样），和/或删除未使用的点和/或删除退化单元。
        sampled_point = vtk.vtkCleanPolyData()
        if self.pointCloud:
            sampled_point.SetInputData(self.pointCloud)
        else:
            sampled_point.SetInputData(self.SceneManager.main_actor.GetMapper().GetInput())
        sampled_point.SetTolerance(tolerance)  # 设置采样度
        sampled_point.Update()
        self.SceneManager.drawPdSrc(sampled_point.GetOutput(), (241 / 255, 135 / 255, 184 / 255), point_size = 3)
        self.SceneManager.display()

    def extract_geometry(self):
        """Extract the outer surface of a volume or structured grid dataset as PolyData.

        This will extract all 0D, 1D, and 2D cells producing the
        boundary faces of the dataset.

        """
        if self.FEModel.ugrid.GetNumberOfPoints() == 0:
            return
            # vtkGeometryFilter，提取来自一个数据集的表面几何，输出为vtkPolyData
        alg = vtk.vtkGeometryFilter()
        alg.SetInputData(self.FEModel.ugrid)
        alg.Update()
        self.SceneManager.drawPdSrc(alg.GetOutput(), opacity = 0.5)
        self.SceneManager.display()

    def TogglePiontPick(self, enable):
        if enable:
            self.SceneManager.piontPick()
        else:
            self.SceneManager.interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())  # 重置交互类型
            self.SceneManager.Clear2D(-1)
            self.SceneManager.Clear3D(-1)
            self.SceneManager.window.Render()

    def ToggleCellPick(self, enable):
        if enable:
            self.SceneManager.cellPick()
        else:
            self.SceneManager.interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())  # 重置交互类型
            self.SceneManager.Clear2D(-1)
            self.SceneManager.Clear3D(-1)
            self.SceneManager.window.Render()

    def meshSimplify(self):
        if self.SceneManager.meshSimplify(ratio = 0.6):
            self.visibilityEdge_action.setChecked(True)

    def meshRefine(self):
        if self.SceneManager.meshRefine(sub_num = 1):
            self.visibilityEdge_action.setChecked(True)

    def pointsVoxelDSampling(self):
        """点云体素下采样"""
        if not self.SceneManager.main_actor:
            return None
        pointCloud = self.SceneManager.main_actor.GetMapper().GetInput()
        if not pointCloud.IsA('vtkPolyData'):
            return None
        source_points = np.array(pointCloud.GetPoints().GetData())
        # 构建KD-Tree寻找最近点
        from scipy import spatial
        tree = spatial.KDTree(data = source_points[:, :3])
        filter_points = voxel_filter(source_points, 5, near = tree)
        filter_cloud = Numpy2vtkPolyData(filter_points)
        self.SceneManager.drawPointCloud(filter_cloud)
        self.SceneManager.display()

    def pointsGradientDSampling(self):
        """点云梯度下采样"""
        if not self.SceneManager.main_actor:
            return None
        pointCloud = self.SceneManager.main_actor.GetMapper().GetInput()
        if not pointCloud.IsA('vtkPolyData'):
            return None
        source_points = np.array(pointCloud.GetPoints().GetData())
        # 获取梯度数据
        filename, _type = QtWidgets.QFileDialog.getOpenFileName(self, '选择梯度文件', self.last_path, '*.csv')
        if not filename:
            return
        G = np.loadtxt(filename, delimiter = ',')
        filter_points = gradient_downsampling(source_points, G.reshape(-1, 1), 2, 5)
        filter_cloud = Numpy2vtkPolyData(filter_points)
        filter_scalars = vtk.vtkFloatArray()
        for i in range(0, len(filter_points)):
            filter_scalars.InsertTuple1(i, filter_points[i][3])
        filter_cloud.GetPointData().SetScalars(filter_scalars)
        # self.SceneManager.drawPointCloud(filter_cloud)
        # 构建颜色映射
        scalarRange = (np.min(filter_points[:, 3]), np.max(filter_points[:, 3]))
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(filter_cloud)
        self.SceneManager.drawScalarField(mapper, scalarRange, title = 'Gradient')
        self.SceneManager.display()

    def dragEnterEvent(self, a0: QtGui.QDragEnterEvent) -> None:  # 拖动进入事件
        if a0.mimeData().hasUrls():
            a0.acceptProposedAction()
        else:
            a0.ignore()

    def dropEvent(self, a0: QtGui.QDropEvent) -> None:  # 放下事件
        mimeData = a0.mimeData()
        if mimeData.hasUrls():
            urlList = mimeData.urls()
            filename = urlList[0].toLocalFile()
            if filename:
                # 绘制图形
                _, suffix = os.path.splitext(filename)
                self.SceneManager.ClearAll()
                if suffix == '*.xyz':  # 点云绘制
                    self.original_model = read_xyz(filename)
                    self.SceneManager.drawPdSrc(self.original_model, (241 / 255, 135 / 255, 184 / 255), point_size = 3)
                elif suffix == '.inp':
                    self.FEModel = FEDataModel()
                    self.FEModel.read_inp(filename)
                    self.SceneManager.drawDsSrc(self.FEModel.ugrid)
                else:
                    self.original_model = ReadPolyData(filename).GetOutput()
                    self.SceneManager.drawPdSrc(self.original_model)
                self.SceneManager.display()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('{}'.format(__appname__))
    app.setOrganizationName('mstifiy')
    win = PinkViwerMainWindow()
    win.show()
    app.exec_()
