# draggable rectangle with the animation blit techniques; see
# http://www.scipy.org/Cookbook/Matplotlib/Animations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.text import Text


class DraggableVehicle:
    lock = None  # only one can be animated at a time
    method = None
    color = None
    showCorr = None

    def __init__(self, figure, vehName, vehicleID, pos):
        self.vehName = vehName
        self.figure = figure
        self.press = None
        self.background = None
        self.release = 0
        self.dragged = None
        self.txt = None
        self.oldLabel = None
        self.newLabel = None
        self.c = 5
        self.name = vehName
        self.offset = 0.4
        self.initalPosx = pos[0]
        self.initalPosy = pos[1]
        self.vehID = vehicleID
        self.vehLength = 0.8
        self.vehHight = 0.8

        self.create_vehicle(figure, vehName)

    def connect(self):
        'connect to all the events we need'
        self.cidpress = self.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_press(self, event):
        'on button press we will see if the mouse is over us and store some data'

        if event.inaxes != self.rect.axes: return
        if DraggableVehicle.lock is not None: return
        contains, attrd = self.rect.contains(event)
        if not contains: return
        print('event contains', self.rect.xy)
        x0, y0 = self.rect.xy
        self.press = x0, y0, event.xdata, event.ydata
        DraggableVehicle.lock = self

        # draw everything but the selected rectangle and store the pixel buffer

        canvas = self.figure.canvas
        axes = self.rect.axes

        self.rect.set_animated(True)
        self.vehText.set_visible(False)

        canvas.draw()
        self.background = canvas.copy_from_bbox(self.rect.axes.bbox)
        self.vehText.set_visible(True)
        # now redraw just the rectangle
        axes.draw_artist(self.rect)

        # and blit just the redrawn area
        canvas.blit(axes.bbox)
        self.method(self.rect.get_label())

        self.color(self.c)

    def on_motion(self, event):
        'on motion we will move the rect if the mouse is over us'
        if DraggableVehicle.lock is not self:
            return
        if event.inaxes != self.rect.axes: return
        x0, y0, xpress, ypress = self.press
        dx = event.xdata - xpress
        dy = event.ydata - ypress
        self.rect.set_x(x0 + dx)
        self.rect.set_y(y0 + dy)

        axes = self.rect.axes

        self.vehText.set_x(x0 + dx)
        self.vehText.set_y(y0 + dy + 0.9)

        canvas = self.figure.canvas

        # restore the background region
        canvas.restore_region(self.background)

        # redraw just the current rectangle
        axes.draw_artist(self.rect)
        axes.draw_artist(self.vehText)

        # blit just the redrawn area
        canvas.blit(axes.bbox)
        self.showCorr(self.rect.xy)

    def on_release(self, event):
        'on release we reset the press data'
        if DraggableVehicle.lock is not self:
            return
        # print('Position is:', self.rect.xy)
        self.press = None
        DraggableVehicle.lock = None
        self.x_pos = self.rect.xy[0]
        self.y_pos = self.rect.xy[1]
        print(self.x_pos, self.y_pos)
        # turn off the rect animation property and reset the background
        self.rect.set_animated(False)
        self.background = None

        # redraw the full figure
        self.figure.canvas.draw()
        self.release = 1
        self.showCorr(self.rect.xy)

    def get_pos(self):
        return self.rect.xy

    def set_pos(self, x, y):
        axes = self.rect.axes

        self.rect.set_x(float(x))
        self.rect.set_y(float(y))

        self.vehText.set_x(float(x))
        self.vehText.set_y(float(y) + 0.9)
        axes.draw_artist(self.vehText)

        canvas = self.figure.canvas
        axes.draw_artist(self.rect)
        canvas.blit(axes.bbox)

        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    def create_vehicle(self, figure, name):

        # Create blue rectangle with label

        for axs in figure.axes:
            print(axs)
            ax = axs
            print(self.initalPosx)
            print(self.initalPosy)
        tmp = ax.bar(self.initalPosx - self.offset, self.vehLength, self.vehHight, self.initalPosy - self.offset, color='blue')

        for rect in tmp:
            self.rect = rect

        self.rect.set_label(int(self.vehID))

        # Create text with label

        self.vehText = ax.text(self.initalPosx - self.offset, self.initalPosy + self.offset*1.1, str(name), label=int(self.vehID))

    def del_veh(self):
        self.rect.remove()
        self.vehText.remove()
        self.figure.canvas.draw()

    def get_name(self):
        return self.vehName

    def disconnect(self):
        'disconnect all the stored connection ids'
        self.figure.canvas.mpl_disconnect(self.cidpos)
        self.figure.canvas.mpl_disconnect(self.cidpress)
        self.figure.canvas.mpl_disconnect(self.cidrelease)
        self.figure.canvas.mpl_disconnect(self.cidmotion)
