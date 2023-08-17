import numpy as np
import vtk
import os
import PyQt5.Qt
import PyQt5.QtGui
from PyQt5.QtCore import QAbstractItemModel, QVariant, QModelIndex, Qt


# vtk
def ReadPolyData(file_name):
    path, extension = os.path.splitext(file_name)
    extension = extension.lower()
    if extension == ".ply":
        reader = vtk.vtkPLYReader()
    elif extension == ".vtp":
        reader = vtk.vtkXMLpoly_dataReader()
    elif extension == ".obj":
        reader = vtk.vtkOBJReader()
    elif extension == ".stl":
        reader = vtk.vtkSTLReader()
    elif extension == ".vtk":
        reader = vtk.vtkPolyDataReader()
        try:
            reader.SetFileName(file_name)
        except Exception:
            reader = vtk.vtkUnstructuredGridReader()
    elif extension == ".g":
        reader = vtk.vtkBYUReader()
    else:
        # Return a None if the extension is unknown.
        return None
    reader.SetFileName(file_name)
    reader.Update()
    return reader


def read_xyz(file_name, numpy = False):
    """Read .xyz file to create vtkPolyData."""
    points = vtk.vtkPoints()  # 点数据
    vertices = vtk.vtkCellArray()  # 单元数据 顶点类型
    n_points = []
    with open(file_name) as f:
        data = f.readlines()
        for d in data:
            xyzd = list(map(float, d.split(' ')))
            n_points.append(xyzd)
            x, y, z = xyzd[0], xyzd[1], xyzd[2]
            # 将每个点的坐标加入vtkPoints，InsertNextPoint() 返回加入点的索引号
            pointId = points.InsertNextPoint(x, y, z)
            # 为每个坐标点分别创建一个顶点，顶点是单元类型里面的一种
            vertices.InsertNextCell(1, [pointId])
    if numpy:
        return np.array(n_points)
    else:
        # 创建vtkPolyData对象
        polyData = vtk.vtkPolyData()
        # 指定数据的几何结构（由points指定）和拓扑结构（由vertices指定）
        polyData.SetPoints(points)
        polyData.SetVerts(vertices)
        return polyData


def WritePolyData(file_name):
    path, extension = os.path.splitext(file_name)
    extension = extension.lower()
    if extension == ".ply":
        writer = vtk.vtkPLYWriter()
    elif extension == ".obj":
        writer = vtk.vtkOBJExporter()
    elif extension == ".stl":
        writer = vtk.vtkSTLWriter()
    elif extension == ".vtk":
        writer = vtk.vtkPolyDataWriter()
    elif extension == ".g":
        writer = vtk.vtkBYUWriter()
    else:
        # Return a None if the extension is unknown.
        return None
    writer.SetFileName(file_name)
    writer.Update()
    return writer


def MakeLUT(colorScheme, lut):
    # See: [Diverging Color Maps for Scientific Visualization]
    #      (http:#www.kennethmoreland.com/color-maps/)
    nc = 256
    ctf = vtk.vtkColorTransferFunction()

    if colorScheme == 1:
        # Green to purple diverging.
        ctf.SetColorSpaceToDiverging()
        ctf.AddRGBPoint(0.0, 0.085, 0.532, 0.201)
        ctf.AddRGBPoint(1.0, 0.436, 0.308, 0.631)
        lut.SetNumberOfTableValues(nc)
        lut.Build()
        for i in range(0, nc):
            rgb = list(ctf.GetColor(float(i) / nc))
            rgb.append(1.0)
            lut.SetTableValue(i, *rgb)
    elif colorScheme == 2:
        # Make a lookup table, black in the centre with bright areas
        #   at the beginning and end of the table.
        # This is from the original code.
        nc2 = nc / 2.0
        lut.SetNumberOfColors(nc)
        lut.Build()
        for i in range(0, int(nc2)):
            # White to black.
            v = (nc2 - i) / nc2
            lut.SetTableValue(i, v, v, v, 1)
        for i in range(int(nc2), nc):
            # Black to white.
            v = (i - nc2) / nc2
            lut.SetTableValue(i, v, v, v, 1)
    else:
        # Cool to warm diverging.
        ctf.SetColorSpaceToDiverging()
        ctf.AddRGBPoint(0.0, 0.230, 0.299, 0.754)
        ctf.AddRGBPoint(1.0, 0.706, 0.016, 0.150)
        lut.SetNumberOfTableValues(nc)
        lut.Build()
        for i in range(0, nc):
            rgb = list(ctf.GetColor(float(i) / nc))
            rgb.append(1.0)
            lut.SetTableValue(i, *rgb)


def UGrid2Pd(ugrid):
    """Convert vtkUnstructuredGrid to vtkPolyData"""
    surface_filter = vtk.vtkDataSetSurfaceFilter()
    surface_filter.SetInputData(ugrid)
    surface_filter.Update()
    return surface_filter.GetOutput()


def Numpy2vtkPolyData(numpy_array):
    vtkPoints = vtk.vtkPoints()
    vtkCellArray = vtk.vtkCellArray()  # 单元数据 顶点类型
    for i in range(0, numpy_array.shape[0]):
        cellId = vtkPoints.InsertNextPoint(numpy_array[i][0], numpy_array[i][1], numpy_array[i][2])
        vtkCellArray.InsertNextCell(1, [cellId])
    vtkPolyData = vtk.vtkPolyData()
    vtkPolyData.SetPoints(vtkPoints)
    vtkPolyData.SetVerts(vtkCellArray)
    return vtkPolyData


def VF2vtkPolyData(V, F):
    points = vtk.vtkPoints()
    cells = vtk.vtkCellArray()  # 单元数据 顶点类型

    for i in range(V.shape[0]):
        points.InsertNextPoint(V[i])
    for i in range(F.shape[0]):
        cells.InsertNextCell(3, F[i])

    vtkPolyData = vtk.vtkPolyData()
    vtkPolyData.SetPoints(points)
    vtkPolyData.SetPolys(cells)

    return vtkPolyData


class FEDataModel:
    """有限元数据模型类"""

    def __init__(self):
        self.nodes = []  # 节点几何坐标
        self.elements = []  # 单元拓扑信息
        self.scalars = {}  # 节点标量属性
        self.vectors = {}  # 节点向量属性
        self.ugrid = vtk.vtkUnstructuredGrid()  # 用于VTK可视化的数据模型
        self.ugrid.Allocate(100)

    def read_inp(self, filename):
        with open(filename) as f:
            node_flag, element_flag = False, False
            for line in f.readlines():
                line = line.replace('\n', '').replace(' ', '')
                if '*ELEMENT' in line:
                    node_flag, element_flag = False, True
                    continue
                elif '*NODE' in line:
                    node_flag, element_flag = True, False
                    continue
                elif '*' in line:
                    node_flag, element_flag = False, False
                    continue
                if node_flag:
                    self.nodes.append(list(map(lambda x: float(x), line.split(',')))[1:])
                elif element_flag:
                    self.elements.append(list(map(lambda x: int(x) - 1, line.split(',')))[1:])
        # print(len(self.nodes), len(self.elements))

        nodes = vtk.vtkPoints()
        for i in range(0, len(self.nodes)):
            nodes.InsertPoint(i, self.nodes[i])

        for i in range(0, len(self.elements)):
            if len(self.elements[i]) == 4:  # 四面体单元
                self.ugrid.InsertNextCell(vtk.VTK_TETRA, 4, self.elements[i])
            elif len(self.elements[i]) == 6:  # 六面体单元
                self.ugrid.InsertNextCell(vtk.VTK_POLYGON, 6, self.elements[i])
            elif len(self.elements[i]) == 3:  # 三角面片单元
                self.ugrid.InsertNextCell(vtk.VTK_TRIANGLE, 3, self.elements[i])
            else:
                print("FEDataModel构建中遇到错误单元类型！")
        self.ugrid.SetPoints(nodes)

    def read_ntl(self, filename):
        with open(filename) as f:
            lines = f.readlines()
            attribute_name = ' '.join(lines[0].split(' ')[1:-1])
            scalar = []
            for line in lines[4:]:
                line = line.replace('\n', '').split(' ')
                scalar.append(float(line[-1]))
            self.scalars[attribute_name] = scalar
        # print(attribute_name + ' scalar number: ' + str(len(scalar)))

        # 存储标量值
        scalars = vtk.vtkFloatArray()
        scalars.SetName(attribute_name)
        for i in range(0, len(scalar)):
            scalars.InsertTuple1(i, scalar[i])
        # 设定每个节点的标量值
        self.ugrid.GetPointData().SetScalars(scalars)
        return scalars

    def read_csv(self, filename):
        scalar = np.loadtxt(filename, delimiter = ",")
        # print('scalar number: ' + str(len(scalar)))
        # 存储标量值
        scalars = vtk.vtkFloatArray()
        scalars.SetName('Scalar Field')
        for i in range(0, len(scalar)):
            scalars.InsertTuple1(i, scalar[i])
        # 设定每个节点的标量值
        self.ugrid.GetPointData().SetScalars(scalars)
        return scalars

    def setScalar(self, scalar):
        # 存储标量值
        scalars = vtk.vtkFloatArray()
        scalars.SetName('Scalar Field')
        for i in range(0, len(scalar)):
            scalars.InsertTuple1(i, scalar[i])
        # 设定每个节点的标量值
        self.ugrid.GetPointData().SetScalars(scalars)

    def display(self):
        renderer = vtk.vtkRenderer()
        renWin = vtk.vtkRenderWindow()
        renWin.AddRenderer(renderer)
        iren = vtk.vtkRenderWindowInteractor()
        iren.SetRenderWindow(renWin)

        colors = vtk.vtkNamedColors()
        ugridMapper = vtk.vtkDataSetMapper()
        ugridMapper.SetInputData(self.ugrid)

        ugridActor = vtk.vtkActor()
        ugridActor.SetMapper(ugridMapper)
        ugridActor.GetProperty().SetColor(colors.GetColor3d("Peacock"))
        ugridActor.GetProperty().EdgeVisibilityOn()

        renderer.AddActor(ugridActor)
        renderer.SetBackground(colors.GetColor3d("Beige"))

        renderer.ResetCamera()
        renderer.GetActiveCamera().Elevation(60.0)
        renderer.GetActiveCamera().Azimuth(30.0)
        renderer.GetActiveCamera().Dolly(1.2)
        renWin.SetSize(640, 480)
        # Interact with the data.
        renWin.Render()
        iren.Start()


def saveXYZ(points, filename = './nodes.xyz'):
    """Save nodes to .xyz file"""
    with open(filename, 'w') as f:
        for node in points:
            for i, n in enumerate(node):
                f.write(str(n))
                if (i + 1) % 3 == 0:
                    f.write('\n')
                else:
                    f.write(' ')
    f.close()


def ugridVectorGenerate(ugrid, save_path = None):
    """基于vtkUnstructuredGrid数据的向量场生成

    :param ugrid: vtkUnstructuredGrid，输入的非结构化网格数据
    :param save_path: 结果VTK文件保存路径，默认不保存
    :return: vtkUnstructuredGrid，含有生成向量场的非结构化网格数据
    """

    def lorentzFunc(sigma, rho, beta):
        return "iHat*%f*(coordsY-coordsX) + jHat*(coordsX*(%f-coordsZ)-coordsY) + kHat*(coordsX*coordsY-%f*coordsZ)" % (
            sigma, rho, beta)

    calc = vtk.vtkArrayCalculator()
    calc.SetInputConnection(ugrid)
    # calc.SetAttributeModeToUsePointData()
    calc.AddCoordinateScalarVariable("coordsX", 0)
    calc.AddCoordinateScalarVariable("coordsY", 1)
    calc.AddCoordinateScalarVariable("coordsZ", 2)
    calc.SetFunction(lorentzFunc(20, 18, 8 / 3.0))
    calc.SetResultArrayName("vectors")
    if save_path:
        writer = vtk.vtkUnstructuredGridWriter()
        writer.SetInputConnection(calc.GetOutputPort())
        writer.SetFileName(save_path)
        writer.Write()
    return calc.GetOutputPort()


# qt
class MyFileTreeItem:

    def __init__(self, data, parent = None):
        self.parentItem = parent  # 父节点
        self.childItems = []  # 子节点
        self.itemData = data  # 子节点对应数据
        self._row = -1  # 此item位于父节点第几个

    def appendChild(self, child):
        child.setRow(len(self.childItems))
        self.childItems.append(child)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        return self.itemData[column]

    # 保存该节点是其父节点的第几个子节点，查询优化所用
    def setRow(self, row: int):
        self._row = row

    # 返回本节点位于父节点下第几个子节点
    def row(self):
        return self._row

    def parent(self):
        return self.parentItem


class MyFileTreeModel(QAbstractItemModel):

    def __init__(self, parent = None):
        super(MyFileTreeModel, self).__init__()
        self.rootItem = None  # 最顶层根节点
        self.updataData([])

    # 在parent节点下，第row行，第column列位置上创建索引
    def data(self, index: QModelIndex, role: int = ...):
        if not index.isValid():
            return QVariant()
        # 添加图标
        if role == Qt.DecorationRole and index.column() == 0:
            return PyQt5.QtGui.QIcon("images/mx.png")
        # 显示节点数据值
        if role == Qt.DisplayRole or role == Qt.WhatsThisRole:
            item = index.internalPointer()
            return item.data(index.column())
        return QVariant()

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return 0
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    # 获取表头数据
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> QVariant:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)
        return QVariant()

    # 在parent节点下，第row行，第column列位置上创建索引
    def index(self, row: int, column: int, parent: QModelIndex = ...) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)  # 展开树形，为子节点建立索引
        else:
            return QModelIndex()

    # 创建index的父索引
    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        childItem = index.internalPointer()
        parentItem = childItem.parent()
        # 顶层节点，直接返回空索引
        if parentItem == self.rootItem:
            return QModelIndex()
        # 为父节点建立索引
        return self.createIndex(parentItem.row(), 0, parentItem)

    # 获取索引parent下有多少行
    def rowCount(self, parent: QModelIndex = ...) -> int:
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        return parentItem.childCount()  # 返回父节点下子节点数目

    # 返回索引parent下有多少列
    def columnCount(self, parent: QModelIndex = ...) -> int:
        return self.rootItem.columnCount()

    # 更新模型数据
    def updataData(self, data):
        """
        模型数据构建，可修改拓展
        :param data: 数据源
        """
        self.beginResetModel()  # 模型重置开始
        # 废弃旧模型数据
        if self.rootItem:
            del self.rootItem
            self.rootItem = None

        rootData = ['FileType']
        self.rootItem = MyFileTreeItem(rootData)
        self._setupModelData(self.rootItem, data)
        self.endResetModel()  # 模型重置结束

    # 构建模型数据
    def _setupModelData(self, parent, data):
        """
        模型数据构建，可修改拓展
        :param parent: MyFileTreeItem,父节点
        :param data: 数据源
        """
        sorted_data = self._sortFiles(data)  # 文件分类
        father_data = sorted_data.keys()
        for data in father_data:
            primary = MyFileTreeItem([data], parent)
            parent.appendChild(primary)
            if len(sorted_data[data]) != 0:
                for ds in sorted_data[data]:
                    primary.appendChild(MyFileTreeItem([ds], primary))

    def _sortFiles(self, fileNames):
        """根据输入的文件名，按文件后缀名进行分类"""
        sorted_data = {'STL几何模型': [], 'VTK文件': [], '体网格模型': [], '点云文件': [], '应力场': [], '温度场': [], '杂项文件': []}
        if len(fileNames) != 0:
            for fn in fileNames:
                suffix = os.path.splitext(fn)[1]  # 读取文件后缀名
                if suffix == '.stl' or suffix == '.STL':
                    sorted_data['STL几何模型'].append(fn)
                elif suffix == '.vtk':
                    sorted_data['VTK文件'].append(fn)
                elif suffix == '.inp':
                    sorted_data['体网格模型'].append(fn)
                elif suffix == '.xtem':
                    sorted_data['温度场'].append(fn)
                elif suffix == '.xyz':
                    sorted_data['点云文件'].append(fn)
                else:
                    sorted_data['杂项文件'].append(fn)
        return sorted_data


# points_processing
def voxel_filter(origin_points, leaf_size, near = False):
    """体素下采样"""
    filtered_points = []
    if near:
        from scipy import spatial
        tree = spatial.KDTree(data = origin_points[:, :3])

    # 计算边界点
    x_min, y_min, z_min = np.amin(origin_points[:, :3], axis = 0)  # 计算x y z 三个维度的最值
    x_max, y_max, z_max = np.amax(origin_points[:, :3], axis = 0)

    # 计算 voxel grid维度
    Dx = (x_max - x_min) // leaf_size + 1
    Dy = (y_max - y_min) // leaf_size + 1
    Dz = (z_max - z_min) // leaf_size + 1
    # print("Dx x Dy x Dz is {} x {} x {}".format(Dx, Dy, Dz))

    # 计算每个点的voxel索引，即确定每个点所被划分到的voxel
    h = []  # h 为保存索引的列表
    for i in range(len(origin_points)):
        hx = (origin_points[i][0] - x_min) // leaf_size
        hy = (origin_points[i][1] - y_min) // leaf_size
        hz = (origin_points[i][2] - z_min) // leaf_size
        h.append(hx + hy * Dx + hz * Dx * Dy)  # voxel索引填充顺序x-y-z
    h = np.array(h)

    # 筛选点
    h_indice = np.argsort(h)  # 返回h里面的元素按从小到大排序的索引
    h_sorted = h[h_indice]
    begin = 0
    for i in range(len(h_sorted)):
        point_idx = h_indice[begin: i + 1]
        if i == len(h_sorted) - 1:  # 到最后一个体素的最后一个点
            if near:
                query_point = np.mean(origin_points[point_idx], axis = 0)[:3]
                _, ind = tree.query(query_point, k = 1)
                filtered_points.append(origin_points[ind])
            else:
                filtered_points.append(np.mean(origin_points[point_idx], axis = 0))  # 计算最后一个体素的采样点
            continue
        if h_sorted[i] == h_sorted[i + 1]:
            continue
        else:
            if near:
                query_point = np.mean(origin_points[point_idx], axis = 0)[:3]
                _, ind = tree.query(query_point, k = 1)
                filtered_points.append(origin_points[ind])
            else:
                filtered_points.append(np.mean(origin_points[point_idx], axis = 0))
            begin = i + 1

    # 把点云格式改成array，并对外返回
    filtered_points = np.array(filtered_points, dtype = np.float64)
    return filtered_points, None


def gradient_downsampling(origin_points, G, a, b):
    """gradient downsampling

    :param origin_points: 原点云
    :param G: 点云梯度值
    :param a: 梯度变化剧烈区域采样体素尺寸
    :param b: 梯度变化缓慢区域采样体素尺寸
    :return: 采样点云
    """
    filtered_points, a_points, b_points = [], [], []
    origin_points = np.hstack((origin_points, G))
    # Step1: 将平均梯度作为梯度阈值
    G_t = np.mean(G)
    # Step2: 根据梯度划分点云为a_points和b_points两个区域
    for i, G_i in enumerate(G):
        if G_i > G_t:
            a_points.append(origin_points[i])
        else:
            b_points.append(origin_points[i])

    # Step3: 采样体素下采样对a_points和b_points两个区域进行采样
    # 构建KD-Tree寻找最近点
    from scipy import spatial
    tree = spatial.KDTree(data = origin_points[:, :3])
    a_filtered, a_index = voxel_filter(np.array(a_points), a, near = True)
    b_filtered, b_index = voxel_filter(np.array(b_points), b, near = True)
    filtered_points = np.vstack((a_filtered, b_filtered))

    return filtered_points


def interpNodes(points, values, xi, method = 'linear', ):
    """节点数据插值

    :param points: 属性已知节点三维坐标集合，即插值空间
    :param values: points对应的属性值
    :param xi: 属性待插值的节点三维坐标集合
    :param method: 插值方法
    :return: xi对应的属性值
    """
    from scipy.interpolate import griddata
    xi_values = griddata(points, values, xi, method = method)
    return xi_values


if __name__ == '__main__':
    # model = FEDataModel()
    # model.read_inp('data/zhujian.inp')
    # model.saveXYZ()
    # SamplingTimeStep()
    nodes = read_xyz('proxyModel/dataset/nodes.xyz', numpy = True)
    nodes_values = np.loadtxt('proxyModel/dataset/csv/zhujian_206.ntlEffective Stress_150.csv',
                              delimiter = ',')
    sampled_nodes = read_xyz('proxyModel/dataset/sampled_nodes.xyz', numpy = True)
    sampled_values = np.loadtxt('predict_result/Result_None_150.0.csv', delimiter = ',')
    interp_nodes_values = interpNodes(sampled_nodes, sampled_values, nodes, method = 'nearest')
    interp_erorr = np.abs(nodes_values - interp_nodes_values)
    print(f'最大插值误差: {np.max(interp_erorr)}\n平均插值误差: {np.mean(interp_erorr)}')
    np.savetxt('interp_nodes_values.csv', interp_nodes_values, delimiter = ',')
