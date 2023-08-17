from PyQt5 import QtCore, QtGui, QtWidgets, Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor as QVTKWidget
from Utilities import MyFileTreeModel


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        self.MainWindow = MainWindow
        self.create_widgets()
        self.create_menu()
        self.m_bSideflag = False  # 是否显示侧边栏

    def create_widgets(self):
        # 实例化一个QWidget，用作中心部件
        self.central_widget = QtWidgets.QWidget(self.MainWindow)
        self.central_widget.setObjectName('central_widget')

        # 设置QTabWidget
        self.tab_widget = QtWidgets.QTabWidget(self.central_widget)
        self.tab_widget.setObjectName("tab_widget")
        # 为tab_widget添加布局尺寸策略
        size_policy_1 = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        size_policy_1.setHorizontalStretch(0)  # 水平伸展0
        size_policy_1.setVerticalStretch(0)  # 垂直伸展0
        size_policy_1.setHeightForWidth(self.tab_widget.sizePolicy().hasHeightForWidth())
        self.tab_widget.setSizePolicy(size_policy_1)

        # 实例化一个QWidget，作为视图区的部件
        self.main_widget = QtWidgets.QWidget(self.central_widget)
        self.main_widget.setObjectName('main_widget')
        # 为main_widget添加布局尺寸策略
        size_policy_2 = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        size_policy_2.setHorizontalStretch(0)  # 水平伸展0
        size_policy_2.setVerticalStretch(0)  # 垂直伸展0
        size_policy_2.setHeightForWidth(self.main_widget.sizePolicy().hasHeightForWidth())
        self.main_widget.setSizePolicy(size_policy_2)

        # 在main_widget上添加vtk控件
        self.vtk_vertical_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.vtk_vertical_layout.setSpacing(0)
        self.vtk_vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.vtk_widget = QVTKWidget(self.main_widget)
        self.vtk_vertical_layout.addWidget(self.vtk_widget)

        # 将中心部件的布局设置为网格布局，将控件添加到布局中
        self.grid_layout = QtWidgets.QGridLayout(self.central_widget)
        self.grid_layout.setObjectName('grid_layout')
        # self.grid_layout.setSpacing(0)
        # self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.addWidget(self.tab_widget, 0, 0, 1, 2)
        self.grid_layout.addWidget(self.main_widget, 1, 0, 1, 1)
        self.setCentralWidget(self.central_widget)

    def set_view_tab(self):
        # 创建view标签页
        self.view_tab = QtWidgets.QWidget()
        self.view_tab.setObjectName('view_tab')
        # 将标签页的布局设置为网格布局，以便有序添加其它控件
        self.view_grid_layout = QtWidgets.QGridLayout(self.view_tab)
        self.view_grid_layout.setObjectName('view_grid_layout')
        # point of view
        self.groupBox = QtWidgets.QGroupBox(self.view_tab)
        self.groupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.groupBox.setObjectName("groupBox")
        self.groupBox.setTitle("Point of view")
        self.pov_vertical_layout = QtWidgets.QVBoxLayout(self.groupBox)
        self.pov_vertical_layout.setObjectName('pov_vertical_layout')
        self.radioButtonXY = QtWidgets.QRadioButton(self.groupBox)
        self.radioButtonXY.setObjectName("radioButtonXY")
        self.radioButtonXY.setChecked(True)
        self.radioButtonXY.setText("XY plane")
        self.radioButtonXY.released.connect(self.SetViewXY)
        self.radioButtonXZ = QtWidgets.QRadioButton(self.groupBox)
        self.radioButtonXZ.setObjectName("radioButtonXZ")
        self.radioButtonXZ.setText("XZ plane")
        self.radioButtonXZ.released.connect(self.SetViewXZ)
        self.radioButtonYZ = QtWidgets.QRadioButton(self.groupBox)
        self.radioButtonYZ.setObjectName("radioButtonYZ")
        self.radioButtonYZ.setText("YZ plane")
        self.radioButtonYZ.released.connect(self.SetViewYZ)
        self.pov_vertical_layout.addWidget(self.radioButtonXY)
        self.pov_vertical_layout.addWidget(self.radioButtonXZ)
        self.pov_vertical_layout.addWidget(self.radioButtonYZ)
        # checkVisualize
        self.checkVisualize_widget = QtWidgets.QWidget(self.view_tab)
        self.checkVisualize_widget.setObjectName("checkVisualize_widget")
        self.checkVisualize_vertical_layout = QtWidgets.QVBoxLayout(self.checkVisualize_widget)
        self.checkVisualize_vertical_layout.setObjectName('checkVisualize_vertical_layout')
        self.checkVisualizeAxis = QtWidgets.QCheckBox(self.view_tab)
        self.checkVisualizeAxis.setObjectName("checkVisualizeAxis")
        self.checkVisualizeAxis.setText("Visualize axis")
        self.checkVisualizeAxis.toggled['bool'].connect(self.ToggleVisualizeAxis)
        self.checkVisibility = QtWidgets.QCheckBox(self.view_tab)
        self.checkVisibility.setChecked(True)
        self.checkVisibility.setObjectName("checkVisibility")
        self.checkVisibility.setText("Show scene")
        self.checkVisibility.toggled['bool'].connect(self.ToggleVisibility)
        self.checkVisualize_vertical_layout.addWidget(self.checkVisualizeAxis)
        self.checkVisualize_vertical_layout.addWidget(self.checkVisibility)
        # 将控件添加到网格布局中，再将标签页添加到QTabWidget中
        self.view_grid_layout.addWidget(self.groupBox, 0, 0, 1, 1)
        self.view_grid_layout.addWidget(self.checkVisualize_widget, 0, 1, 1, 1)
        self.tab_widget.addTab(self.view_tab, '视图')

    def create_menu(self):
        self.setup_file_menu()
        self.setup_view_menu()
        self.setup_visualization_menu()
        self.setup_FEPost_menu()
        self.setup_mesh_menu()
        self.setup_pointCloud_menu()
        self.setup_help_menu()
        self.statusbar = self.statusBar()
        self.statusbar.setSizeGripEnabled(False)  # 不显示状态栏右下角抓痕

    def create_action(self, text,  # 显示文本
                      slot = None,  # 槽函数
                      shortcut = None,  # 快捷键
                      icon = None,  # 图标
                      tip = None,  # 提示信息
                      checkable = False,  # 可点击
                      signal = 'triggered'):
        action = QtWidgets.QAction(text, self.MainWindow)
        if icon is not None:
            action.setIcon(QtGui.QIcon(icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            getattr(action, signal).connect(slot)
        if checkable:
            action.setCheckable(True)
        return action

    @staticmethod
    def add_actions(target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()  # 添加分隔线
            else:
                target.addAction(action)

    def setup_file_menu(self):
        file_menu = self.menuBar().addMenu('文件')
        file_toolbar = self.addToolBar('文件')
        file_toolbar.setObjectName('file_toolbar')
        file_open_action = self.create_action('打开文件', self.file_open, QtGui.QKeySequence.Open, 'images/fileopen')
        folder_open_action = self.create_action('打开文件夹', self.folder_open, icon = 'images/folderopen')
        meshFile_save_action = self.create_action('保存网格模型', self.save_mesh, icon = 'images/save')
        file_quit_action = self.create_action('退出', self.close, 'Ctrl+Q', 'images/quit')
        self.add_actions(file_menu,
                         (file_open_action, folder_open_action, meshFile_save_action, None, file_quit_action))
        self.add_actions(file_toolbar, (file_open_action, folder_open_action, file_quit_action))

    def setup_view_menu(self):
        view_menu = self.menuBar().addMenu('视图')
        view_toolbar = self.addToolBar('视图')
        view_toolbar.setObjectName('view_toolbar')
        view_fit_action = self.create_action('适合窗口', self.fit_all, 'Ctrl+F', 'images/fit', '适合窗口')
        self.visualize_axis_action = self.create_action('显示坐标系', self.ToggleVisualizeAxis, 'Ctrl+L', checkable = True,
                                                        signal = 'toggled')
        self.visibility_action = self.create_action('显示图形', self.ToggleVisibility, checkable = True,
                                                    signal = 'toggled')
        self.visibilityEdge_action = self.create_action('显示线框', self.ToggleVisibilityEdge, icon = 'images/grid',
                                                        checkable = True,
                                                        signal = 'toggled')
        outline_action = self.create_action('显示外轮廓线', self.ToggleOutline, icon = 'images/outline', checkable = True,
                                            signal = 'toggled')
        silhouette_action = self.create_action('显示外轮廓', self.ToggleSilhouette, checkable = True, signal = 'toggled')
        take_snapshot_action = self.create_action('快照', self.Snapshot, icon = 'images/snapshot', tip = 'Take snapshot')
        clear_all_action = self.create_action('清空窗口', self.ClearAll, icon = 'images/clear')
        opacity_action = self.create_action('透明显示', self.ToggleOpacity, checkable = True, signal = 'toggled')
        self.add_actions(view_menu,
                         (view_fit_action, self.visibilityEdge_action, self.visualize_axis_action,
                          self.visibility_action, outline_action, opacity_action, silhouette_action,
                          take_snapshot_action))
        self.add_actions(view_toolbar, (view_fit_action, clear_all_action, self.visibilityEdge_action))

    def setup_visualization_menu(self):
        visualization_menu = self.menuBar().addMenu('可视化操作')
        visualization_toolbar = self.addToolBar('可视化操作')
        visualization_toolbar.setObjectName('visualization_toolbar')
        vis_curvatures_field_action = self.create_action('模型曲率', self.show_curvatures_field,
                                                         icon = 'images/curvatures1',
                                                         tip = '计算并显示模型曲率场')
        load_scalarField_action = self.create_action('加载属性', self.loadScalarField, icon = 'images/scalar_file')
        diff_file_action = self.create_action('属性比较', self.calDifference, icon = 'images/diff_file', tip = '计算两个属性的差值')
        mesh2points_action = self.create_action('显示模型点云', self.mesh2points, icon = 'images/mesh2points')
        samplingPoints_action = self.create_action('采样点云', self.samplingPoints, icon = 'images/sampling')
        extract_geometry_action = self.create_action('提取网格', self.extract_geometry, icon = 'images/extract_geometry',
                                                     tip = '提取有限元模型的表面网格')
        pick_point_action = self.create_action('拾取点', self.TogglePiontPick, icon = 'images/point_picker',
                                               checkable = True, signal = 'toggled')
        pick_cell_action = self.create_action('拾取单元', self.ToggleCellPick, icon = 'images/cell_pick', checkable = True,
                                              signal = 'toggled')
        self.add_actions(visualization_menu, (vis_curvatures_field_action, load_scalarField_action, diff_file_action))
        self.add_actions(visualization_toolbar,
                         (vis_curvatures_field_action, load_scalarField_action, diff_file_action, mesh2points_action,
                          samplingPoints_action, extract_geometry_action, pick_point_action, pick_cell_action))

    def setup_FEPost_menu(self):
        FEPost_menu = self.menuBar().addMenu('有限元后处理')
        FEPost_toolbar = self.addToolBar('可视化操作')
        FEPost_toolbar.setObjectName('FEPost_toolbar')
        loadINPFile_action = self.create_action('加载inp文件', self.load_INP_file)
        loadNTLFile_action = self.create_action('加载ntl文件', self.load_NTL_file, icon = 'images/scalar')
        save_FEModel_action = self.create_action('保存有限元模型', self.save_femodel, icon = 'images/save')
        load_vtkFEModel_action = self.create_action('加载vtk有限元模型', self.load_vtkFEModel)
        clip_view_action = self.create_action('剖切视图', self.clip_view, icon = 'images/clip')
        isosurface_view_action = self.create_action('等值面视图', self.isosurface_extraction, icon = 'images/isofaces')
        bounding_box_view_action = self.create_action('包围盒', self.ToggleVisibilityBB, icon = 'images/boundingBox',
                                                      checkable = True, signal = 'toggled')
        self.add_actions(FEPost_menu,
                         (loadINPFile_action, loadNTLFile_action, None, load_vtkFEModel_action, save_FEModel_action,
                          None, clip_view_action, isosurface_view_action, bounding_box_view_action, None))
        self.add_actions(FEPost_toolbar, (clip_view_action, isosurface_view_action, bounding_box_view_action))

    def setup_mesh_menu(self):
        mesh_menu = self.menuBar().addMenu('网格操作')
        mesh_toolbar = self.addToolBar('网格操作')
        mesh_toolbar.setObjectName('mesh_toolbar')
        mesh_simplify_action = self.create_action('网格简化', self.meshSimplify)
        mesh_refine_action = self.create_action('网格细化', self.meshRefine)
        self.add_actions(mesh_menu, (mesh_simplify_action, mesh_refine_action))

    def setup_pointCloud_menu(self):
        pointCloud_menu = self.menuBar().addMenu('点云操作')
        pointCloud_toolbar = self.addToolBar('网格操作')
        pointCloud_toolbar.setObjectName('pointCloud_toolbar')
        voxel_downSampling_action = self.create_action('体素下采样', self.pointsVoxelDSampling)
        gradient_downSampling_action = self.create_action('梯度下采样', self.pointsGradientDSampling)
        self.add_actions(pointCloud_menu, (voxel_downSampling_action, gradient_downSampling_action))

    def setup_help_menu(self):
        help_menu = self.menuBar().addMenu('帮助')
        help_action = self.create_action('帮助', self.help, icon = 'images/help', tip = '帮助')
        about_action = self.create_action('关于', self.about, icon = 'images/info', tip = '关于')
        self.add_actions(help_menu, (help_action, about_action))
