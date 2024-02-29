import sys
import copy
import time
import random
from tools import GameStateMachine
from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import QTimer, QRectF, Qt, QPropertyAnimation, QPointF
from PyQt6.QtGui import QBrush, QColor, QPixmap, QPen


class Demo(QtWidgets.QMainWindow):
    def __init__(self, r_size: int, c_size: int, scale: int):
        super(Demo, self).__init__()

        self.frame_time = 50
        self.r_size = r_size
        self.c_size = c_size
        self.scale = scale
        self.refill_timer: QTimer = QTimer()  # 每次检查消除后定期调用下落和填充，实现下落视觉效果
        self.gem_pixmaps: dict[QPixmap] = {
            0: QPixmap("0.png").scaled(
                self.scale, self.scale, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ),
            1: QPixmap("1.png").scaled(
                self.scale, self.scale, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ),
            2: QPixmap("2.png").scaled(
                self.scale, self.scale, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ),
            3: QPixmap("3.png").scaled(
                self.scale, self.scale, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ),
            4: QPixmap("4.png").scaled(
                self.scale, self.scale, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ),
        }
        self.highlighted: list[QtWidgets.QGraphicsRectItem] = []

        self.gem_state: list[list[int]] = []
        self.gem_graph: list[list[QtWidgets.QGraphicsPixmapItem]] = []
        self.selected_gems: list[tuple] = []
        ui = uic.loadUi("main.ui", self)

        # 获取控件
        self.start_button: QtWidgets.QPushButton = ui.start_button
        self.view: QtWidgets.QGraphicsView = ui.view
        self.scene = QtWidgets.QGraphicsScene(self)

        # 连接信号
        self.start_button.clicked.connect(self.game_start)
        self.refill_timer.timeout.connect(self.refill_once)

        # 点击事件
        self.scene.mousePressEvent = self.gem_clicked

        # 初始化
        self.ini_board()

        # 将Scene应用到view并调整view大小
        self.view.setScene(self.scene)
        self.view.setStyleSheet("padding: 0px; border: 0px;")
        self.view.setGeometry(50, 50, int(self.scene.sceneRect().width()) + 50, int(self.scene.sceneRect().height() + 50))

    # 断开信号，随机宝石数组，绘制填充，检查消除
    def game_start(self):
        self.start_button.clicked.disconnect()
        self.gem_state = [[random.randint(1, 4) for _ in range(self.c_size)] for _ in range(self.r_size)]
        self.draw_board()
        self.update()

    # 初始化全部黑色填充
    def ini_board(self):
        for i in range(self.r_size):
            row = []
            for j in range(self.c_size):
                # 准备图片
                pixmap = QPixmap("0.png")
                pixmap = pixmap.scaled(
                    self.scale,
                    self.scale,
                    aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                    transformMode=Qt.TransformationMode.SmoothTransformation,
                )
                # 生成item并应用图片纹理
                gem = QtWidgets.QGraphicsRectItem(j * self.scale, i * self.scale, self.scale, self.scale)
                gem.setBrush(QBrush(pixmap))
                self.scene.addItem(gem)
                row.append(gem)
            self.gem_graph.append(row)

    # 绘制填充
    def draw_board(self):
        for i in range(self.r_size):
            for j in range(self.c_size):
                pixmap = QPixmap(f"{self.gem_state[i][j]}.png")
                pixmap = pixmap.scaled(
                    self.scale,
                    self.scale,
                    aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                    transformMode=Qt.TransformationMode.SmoothTransformation,
                )
                self.gem_graph[i][j].setBrush(QBrush(pixmap))

    # 检查消除并调用填充和掉落方法
    def update(self):

        to_eliminate = [[False] * self.c_size for _ in range(self.r_size)]

        # 检查行
        for i in range(self.r_size):
            for j in range(self.c_size - 2):
                if (
                    self.gem_state[i][j] != 0
                    and self.gem_state[i][j] == self.gem_state[i][j + 1] == self.gem_state[i][j + 2]
                ):
                    # 找到连续的宝石，向右扩展
                    k = j
                    while k < self.c_size and self.gem_state[i][j] == self.gem_state[i][k]:
                        to_eliminate[i][k] = True
                        k += 1

        # 检查列
        for j in range(self.c_size):
            for i in range(self.r_size - 2):
                if (
                    self.gem_state[i][j] != 0
                    and self.gem_state[i][j] == self.gem_state[i + 1][j] == self.gem_state[i + 2][j]
                ):
                    # 找到连续的宝石，向下扩展
                    k = i
                    while k < self.r_size and self.gem_state[i][j] == self.gem_state[k][j]:
                        to_eliminate[k][j] = True
                        k += 1

        # 执行消除
        eliminated = False
        for i in range(self.r_size):
            for j in range(self.c_size):
                if to_eliminate[i][j]:
                    self.gem_state[i][j] = 0
                    eliminated = True

        # 如果进行了消除，开始执行填充
        if eliminated:
            self.draw_board()
            QtWidgets.QApplication.processEvents()
            self.refill_timer.start(self.frame_time)
        # 交换后没有消除，再交换回去
        else:
            if len(self.selected_gems) == 2:
                i1, j1, i2, j2 = (
                    self.selected_gems[0][0],
                    self.selected_gems[0][1],
                    self.selected_gems[1][0],
                    self.selected_gems[1][1],
                )
                self.gem_state[i1][j1], self.gem_state[i2][j2] = self.gem_state[i2][j2], self.gem_state[i1][j1]
                self.draw_board()

        # 无论消除与否，都清空选中的宝石的列表
        self.selected_gems.clear()

    # 由timer定时触发，每次只掉落一格或者在第一行生成新宝石，如果没有产生操作，则结束计时并调用update继续检查消除
    def refill_once(self):
        something_changed = False
        # 如果第一行有空格，就生成一个
        for j in range(self.c_size):
            if self.gem_state[0][j] == 0:
                self.gem_state[0][j] = random.randint(1, 4)
                something_changed = True

        # 如果下方有空格，则掉落一格，且掉落后i+1，避免同一个宝石一直掉到底
        for j in range(self.c_size):
            for i in range(self.r_size - 1):
                if self.gem_state[i][j] != 0 and self.gem_state[i + 1][j] == 0:
                    self.gem_state[i + 1][j] = self.gem_state[i][j]
                    self.gem_state[i][j] = 0
                    i = i + 1
                    something_changed = True

        self.draw_board()
        QtWidgets.QApplication.processEvents()

        if not something_changed:
            self.refill_timer.stop()
            self.update()

    def gem_clicked(self, event):
        item: QtWidgets.QGraphicsRectItem = self.scene.itemAt(event.scenePos(), self.view.transform())
        if item:
            i, j = int(item.rect().y() / self.scale), int(item.rect().x() / self.scale)
            self.selected_gems.append((i, j))

            # 获取被点击项的边界
            rect = item.boundingRect()
            # 创建一个矩形框来作为高亮显示
            highlight = QtWidgets.QGraphicsRectItem(rect)
            highlight.setPen(QPen(QColor("yellow"), 3))
            # 将高亮框添加到同一个 scene 中，并设置其位置与被点击项相同
            highlight.setPos(item.pos())
            self.highlighted.append(highlight)
            self.scene.addItem(highlight)

            print(self.selected_gems)

        if len(self.selected_gems) == 2:
            i1, j1, i2, j2 = (
                self.selected_gems[0][0],
                self.selected_gems[0][1],
                self.selected_gems[1][0],
                self.selected_gems[1][1],
            )
            # 移除选中框
            for highlight in self.highlighted:
                self.scene.removeItem(highlight)
                highlight = None

            # 只有相邻的才可以交换
            if abs(i1 - i2) == 1 or abs(j1 - j2) == 1:
                self.gem_state[i1][j1], self.gem_state[i2][j2] = self.gem_state[i2][j2], self.gem_state[i1][j1]
                self.draw_board()
                QtWidgets.QApplication.processEvents()
                QTimer.singleShot(500, self.update)  # 每次交换后等一段时间，实现视觉上交换之后的画面
            else:
                self.selected_gems.clear()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    game = Demo(10, 10, 64)
    game.show()
    sys.exit(app.exec())
