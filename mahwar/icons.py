"""Crisp vector navigation icons, drawn without third-party icon fonts."""
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QPainterPath

def icon_for(route: str, color: str = "#424359") -> QIcon:
    pixmap = QPixmap(48, 48)
    pixmap.fill(Qt.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.scale(2, 2)
    pen = QPen(QColor(color), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    def line(x1,y1,x2,y2):
        p.drawLine(QPointF(x1,y1), QPointF(x2,y2))
    def circle(x,y,r):
        p.drawEllipse(QPointF(x,y),r,r)
    if route == "dashboard":
        roof=QPainterPath()
        roof.moveTo(3,11);roof.lineTo(12,3);roof.lineTo(21,11)
        p.drawPath(roof)
        p.drawRoundedRect(QRectF(5,10,14,11),1,1)
        line(10,21,10,15);line(10,15,14,15);line(14,15,14,21)
    elif route == "week":
        p.drawRoundedRect(QRectF(3,5,18,16),2,2)
        line(3,10,21,10);line(8,3,8,7);line(16,3,16,7)
        for x in (8,12,16):
            for y in (14,18):
                circle(x,y,.55)
    elif route == "tasks":
        p.drawRoundedRect(QRectF(4,4,16,16),2,2)
        line(8,12,11,15);line(11,15,17,9)
    elif route == "reminders":
        shape=QPainterPath()
        shape.moveTo(6,17);shape.lineTo(8,14);shape.lineTo(8,10)
        shape.cubicTo(8,4,16,4,16,10)
        shape.lineTo(16,14);shape.lineTo(18,17);shape.closeSubpath()
        p.drawPath(shape);line(6,17,18,17);p.drawArc(QRectF(10,17,4,4),180*16,180*16)
    elif route == "focus":
        circle(12,12,9);line(12,12,12,6);line(12,12,16,14)
    elif route == "review":
        p.drawRoundedRect(QRectF(5,3,14,18),1.5,1.5)
        for y in (8,12,16):
            circle(9,y,.5);line(12,y,16,y)
    elif route == "settings":
        circle(12,12,5)
        circle(12,12,2)
        for dx,dy in ((0,-9),(0,9),(-9,0),(9,0),(-6,-6),(6,6),(-6,6),(6,-6)):
            line(12+dx*.75,12+dy*.75,12+dx,12+dy)
    p.end()
    return QIcon(pixmap)
