import os
import rospy
import rospkg
import sys
import std_msgs.msg
import formation_control.msg
import random
import math

from qt_gui.plugin import Plugin
from python_qt_binding import loadUi
from python_qt_binding.QtWidgets import QWidget
from std_msgs.msg import String
from PyQt5 import uic
from std_msgs.msg import String
from std_msgs.msg import Bool
from formation_control.msg import Formation

import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtWidgets import QDialog, QApplication
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from numpy import *
from PyQt5.QtWidgets import QMainWindow, QLabel, QWidget, QPushButton, QAction, QLineEdit, QMessageBox, QPlainTextEdit, QTextEdit, QVBoxLayout
from PyQt5.QtGui import QIcon, QLinearGradient, QRadialGradient
from PyQt5.QtCore import pyqtSlot
from PyQt5.Qt import QApplication, QClipboard
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QSize
from PyQt5 import QtGui

from matplotlib.text import Text
from matplotlib.figure import Figure

from draggable_vehicle import DraggableVehicle


class VehicleControl(Plugin):

    def __init__(self, context):

        super(VehicleControl, self).__init__(context)
        # Give QObjects reasonable names
        self.setObjectName('MyPlugin')

        # Process standalone plugin command-line arguments
        from argparse import ArgumentParser
        parser = ArgumentParser()
        # Add argument(s) to the parser.
        parser.add_argument("-q", "--quiet", action="store_true",
                            dest="quiet",
                            help="Put plugin in silent mode")
        args, unknowns = parser.parse_known_args(context.argv())
        if not args.quiet:
            print 'arguments: ', args
            print 'unknowns: ', unknowns

        # Create QWidget

        self._widget = QWidget()
        # Get path to UI file which should be in the "resource" folder of this package
        ui_file = os.path.join(rospkg.RosPack().get_path('rqt_mypkg'), 'resource', 'formation_control.ui')

        # Extend the widget with all attributes and children from UI file
        loadUi(ui_file, self._widget)
        self.ui=uic.loadUi(ui_file, self._widget)

        self.vehNames = ['Cres', 'Losinj', 'Krk', 'Vis', 'Mljet']
        self.tmpVehNames = ['Cres', 'Losinj', 'Krk', 'Vis', 'Mljet']
        self.vehID = [0, 1, 2, 3, 4]
        self.pos_x = 1
        self.pos_y = 1
        self.textList = []
        self.vehicles = []
        self.vehCounter = 0
        self.x_corr = [None]*len(self.vehNames)
        self.y_corr = [None]*len(self.vehNames)
        self.x_shape = [0]*len(self.vehNames)**2
        self.y_shape = [0]*len(self.vehNames)**2
        self.vehCounter = 0
        self.vehLenght = 0.8
        self.offset = self.vehLenght/2
        self.select = False


        #Rostopic

        global pubFCEnable, pubFormChange
        pubFCEnable = rospy.Publisher('FCEnable', std_msgs.msg.Bool, queue_size=10)
        pubFormChange = rospy.Publisher('FormChange', formation_control.msg.Formation, queue_size=10)

        #figure plot

        plt.ioff()

        self.figure = plt.gcf()
        self.canvas = FigureCanvas(self.figure)
        self.figure.set_facecolor("none")
        plt.close(self.figure)
        self.canvas.setStyleSheet("background-color:transparent;")

        self._widget.plot_layout.addWidget(self.canvas)
        self.xLim0 = 5
        self.yLim0 = 5

        self._widget.xLim.setText(str(self.xLim0))
        self._widget.yLim.setText(str(self.yLim0))
        global ax
        ax = self.figure.add_subplot(111, axisbg='#76a4ed')
        ax.set_xlim(0, self.xLim0)
        ax.set_ylim(0, self.yLim0)
        ax.grid()
        plt.show()

        self._widget.setObjectName('MyPluginUi')

        # Show _widget.windowTitle on left-top of each plugin (when
        # it's set in _widget). This is useful when you open multiple
        # plugins at once. Also if you open multiple instances of your
        # plugin at once, these lines add number to make it easy to
        # tell from pane to pane.


        self._widget.pubFormChange_button.clicked.connect(self.pub_FormChange)
        self._widget.add_vehicle.clicked.connect(lambda: self.add_vehicle(self.pos_x, self.pos_y))
        self._widget.set_lim.clicked.connect(self.set_limits)
        self._widget.delete_vehicle.clicked.connect(lambda: self.delete_vehicle(True, False))
        self._widget.set_button.clicked.connect(self.set_position)
        self._widget.vehForm_3.clicked.connect(self.veh3_formation)
        self._widget.vehForm_4.clicked.connect(self.veh4_formation)
        self._widget.vehForm_5.clicked.connect(self.veh5_formation)
        self._widget.pb_start.clicked.connect(self.pub_FCEnable_msgs_start)
        self._widget.pb_stop.clicked.connect(self.pub_FCEnable_msgs_stop)

        self._widget.vehForm_3.setCheckable(True)
        self._widget.vehForm_4.setCheckable(True)
        self._widget.vehForm_5.setCheckable(True)

        self._widget.plainTextEdit.insertPlainText("Nothing to show.")
        self.xedit = self._widget.xEdit
        self.yedit = self._widget.yEdit

        if context.serial_number() > 1:
            self._widget.setWindowTitle(self._widget.windowTitle() + (' (%d)' % context.serial_number()))
        # Add widget to the user interface
        context.add_widget(self._widget)


    def read_position(self, sometext):
        xcorr = self.xedit.text()
        ycorr = self.yedit.text()
        print(xcorr)
        print(ycorr)
        self.lbl.setText(self.xedit.text())



    def add_vehicle(self, x, y):

        name = next((item for item in self.vehNames if item is not None), 'All are Nones')
        ind = int(self.vehNames.index(name))
        self.vehNames[int(ind)] = None


        veh_id = next((item for item in self.vehID if item is not None), 'All are Nones')
        self.vehID[(int(self.vehID.index(veh_id)))] = None

        position = [x - self.offset, y-self.offset]

        vehicle = DraggableVehicle(self.figure, name, veh_id, position)
        vehicle.connect()
        vehicle.method = self.get_id
        vehicle.color = self.change_color
        vehicle.showCorr = self.show_corr

        print(self.vehID)
        self.vehicles.append(vehicle)
        self.vehCounter = self.vehCounter + 1
        print ('Vehicles on the map:', self.vehCounter)

        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

        if self.vehCounter > 0:
            self._widget.delete_vehicle.setEnabled(True)
        if self.vehCounter == 5:
            self._widget.add_vehicle.setEnabled(False)

    def shutdown_plugin(self):
        # TODO unregister all publishers here
        pass


    def get_id(self, id):
        self.vehicle_id = id


    def show_corr(self, xy):

        self._widget.xEdit.setText(str(xy[0] + self.offset))
        self._widget.yEdit.setText(str(xy[1] + self.offset))

    def change_color(self, a):

        for vehicle in self.vehicles:
            if vehicle.rect.get_label() != self.vehicle_id:
                vehicle.rect.set_color('blue')
            else:
                vehicle.rect.set_color('green')
                self.select = True

    def veh3_formation(self):

        try:
            float(self._widget.distanceEdit.text())
        except ValueError:
            self._widget.vehForm_3.toggle()
            self.change_plain_text('Wrong input! (expected int or float)')
        else:
            if self._widget.distanceEdit.text() == '':
                self.change_plain_text('Enter distance between vehicles!!!')
                self._widget.vehForm_3.toggle()

            else:
                if float(self._widget.distanceEdit.text()) < 1:
                    self.change_plain_text('Distance is to small. Enter Larger distance between vehicles!')
                    self._widget.vehForm_3.toggle()

                else:
                    self.change_plain_text('')
                    distanceTemp = float(self._widget.distanceEdit.text())
                    if len(self.vehicles) > 0:
                        self.delete_vehicle(False, True)
                        self.add_vehicle(1, 1)
                        self.add_vehicle(distanceTemp + 1, 1)
                        self.add_vehicle(distanceTemp / 2 + 1, sqrt((distanceTemp ** 2) - (distanceTemp / 2) ** 2) + 1)
                    else:
                        self.add_vehicle(1, 1)
                        self.add_vehicle(distanceTemp + 1, 1)
                        self.add_vehicle(distanceTemp / 2 +1, sqrt((distanceTemp ** 2) - (distanceTemp / 2) ** 2) + 1)


                if self._widget.vehForm_4.isChecked():
                    self._widget.vehForm_4.toggle()
                if self._widget.vehForm_5.isChecked():
                    self._widget.vehForm_5.toggle()

                if self.vehCounter < 5:
                    self._widget.add_vehicle.setEnabled(True)

    def veh4_formation(self):

        try:
            float(self._widget.distanceEdit.text())
        except ValueError:
            self._widget.vehForm_4.toggle()
            self.change_plain_text('Wrong input! (expected int or float)')
        else:
            if self._widget.distanceEdit.text() == '':
                self.change_plain_text('Enter distance between vehicles!!!')
                self._widget.vehForm_4.toggle()

            else:
                if float(self._widget.distanceEdit.text()) < 1:
                    self.change_plain_text('Distance is to small. Enter Larger distance between vehicles!')
                    self._widget.vehForm_4.toggle()

                else:
                    distanceTemp = float(self._widget.distanceEdit.text())
                    if len(self.vehicles) > 0:
                        self.delete_vehicle(False, True)
                        self.add_vehicle(1, 1)
                        self.add_vehicle(distanceTemp + 1, 1)
                        self.add_vehicle(distanceTemp + 1, distanceTemp + 1)
                        self.add_vehicle(1, distanceTemp + 1)
                    else:
                        self.add_vehicle(1, 1)
                        self.add_vehicle(distanceTemp + 1, 1)
                        self.add_vehicle(distanceTemp + 1, distanceTemp + 1)
                        self.add_vehicle(1, distanceTemp + 1)


                if self._widget.vehForm_3.isChecked():
                    self._widget.vehForm_3.toggle()
                if self._widget.vehForm_5.isChecked():
                    self._widget.vehForm_5.toggle()

                if self.vehCounter < 5:
                    self._widget.add_vehicle.setEnabled(True)

    def veh5_formation(self):

        try:
            float(self._widget.distanceEdit.text())
        except ValueError:
            self._widget.vehForm_5.toggle()
            self.change_plain_text('Wrong input! (expected int or float)')
        else:
            if self._widget.distanceEdit.text() == '':
                self.change_plain_text('Enter distance between vehicles!!!')
                self._widget.vehForm_5.toggle()

            else:
                if float(self._widget.distanceEdit.text()) < 1:
                    self.change_plain_text('Distance is to small. Enter Larger distance between vehicles!')
                    self._widget.vehForm_4.toggle()

                else:
                    distanceTemp = float(self._widget.distanceEdit.text())
                    if len(self.vehicles) > 0:
                        self.delete_vehicle(False, True)
                        self.add_vehicle(3, 1)
                        self.add_vehicle(1, 2)
                        self.add_vehicle(2, 5)
                        self.add_vehicle(4, 5)
                        self.add_vehicle(5, 2)
                    else:
                        self.add_vehicle(3, 1)
                        self.add_vehicle(1, 2)
                        self.add_vehicle(2, 5)
                        self.add_vehicle(4, 5)
                        self.add_vehicle(5, 2)


                if self._widget.vehForm_3.isChecked():
                    self._widget.vehForm_3.toggle()
                if self._widget.vehForm_4.isChecked():
                    self._widget.vehForm_4.toggle()

                if self.vehCounter < 5:
                    self._widget.add_vehicle.setEnabled(True)

    def set_position(self):
        try:
            float(self._widget.xEdit.text())
            float(self._widget.yEdit.text())
        except ValueError:
            self.change_plain_text('Wrong input! (expected int or float)')
        else:
            x = float(self._widget.xEdit.text())
            y = float(self._widget.yEdit.text())
            for veh in self.vehicles:

                if int(veh.rect.get_label()) == int(self.vehicle_id):
                    self.vehicles[int(self.vehicles.index(veh))].set_pos(x - self.offset,y - self.offset)

            print('Vehicles on the map:', self.vehCounter)

            if self.vehCounter == 0:
                self._widget.delete_vehicle.setEnabled(False)

            if self.vehCounter < 5:
                self._widget.add_vehicle.setEnabled(True)

    def save_settings(self, plugin_settings, instance_settings):
        """

        :param plugin_settings:
        :param instance_settings:
        :return:
        """
        # TODO save intrinsic configuration, usually using:
        # instance_settings.set_value(k, v)
        pass

    def restore_settings(self, plugin_settings, instance_settings):
        # TODO restore intrinsic configuration, usually using:
        # v = instance_settings.value(k)
        pass

    #def trigger_configuration(self):
        # Comment in to signal that the plugin has a way to configure
        # This will enable a setting button (gear icon) in each dock widget title bar
        # Usually used to open a modal configuration dialog

        # def publish_start(self):
        # print "Publisher"

    def pub_FCEnable_msgs_start(self):
        pubFCEnable.publish(std_msgs.msg.Bool(True))

    def pub_FCEnable_msgs_stop(self):
        pubFCEnable.publish(std_msgs.msg.Bool(False))

    def pub_FormChange(self):


        if self._widget.shapeCheckBox.isChecked() and self._widget.rotationCheckBox.isChecked() == False:
            self.change_plain_text('Shape selected (shape enable set: True), rotation angle not selected (rootation enable set: False)')
            print('Shape set: True')
            tmp = formation_control.msg.Formation()
            tmp.shape.enable = True
            corr = self.get_corr()
            print(corr)
            tmp.shape.x = self.x_shape
            tmp.shape.y = self.y_shape
            pubFormChange.publish(tmp)

        if self._widget.shapeCheckBox.isChecked() and self._widget.rotationCheckBox.isChecked():
            self.change_plain_text('Shape selected (shape enable set: True), rotation angle selected (rootation enable set: True)')

            if self._widget.angleEdit.text() != '':
                tmp = formation_control.msg.Formation()
                try:
                    tmp.rotation.angle = float(self._widget.angleEdit.text())
                except ValueError:
                    self.change_plain_text('Wrong input! (expected int or float)')
                    return
                tmp.shape.enable = True
                corr = self.get_corr()
                print(corr)
                tmp.shape.x = self.x_shape
                tmp.shape.y = self.y_shape
                tmp.rotation.enable = True
                pubFormChange.publish(tmp)
            else:
                self.change_plain_text('Enter angle!')


        if self._widget.shapeCheckBox.isChecked() == False and self._widget.rotationCheckBox.isChecked() == False:
            self.change_plain_text('Shape not selected!')
            print('Shape set: False, rotation set: False')

        if self._widget.shapeCheckBox.isChecked() == False and self._widget.rotationCheckBox.isChecked():
            self.change_plain_text('Shape not selected (shape enable set: False), rotation angle selected (rootation enable set: True)')
            tmp = formation_control.msg.Formation()
            tmp.shape.enable = False

            if self._widget.angleEdit.text() != '':
                try:
                    tmp.rotation.angle = float(self._widget.angleEdit.text())
                except ValueError:
                    self.change_plain_text('Wrong input! (expected int or float)')
                    return
                tmp.rotation.enable = True
            else:
                self.change_plain_text('Enter angle!')
            pubFormChange.publish(tmp)


    def callback(self, data):
        rospy.loginfo(rospy.get_caller_id() + '\n I heard %s', data.data)
        # self.a = rospy.get_caller_id() + '\n I heard {}'.format(data.data)
        #print(rospy.get_caller_id())
        # print("CALLBACK : {}".format(self.a))

    def delete_vehicle(self, oneVeh, allVeh):

        if self._widget.vehForm_3.isChecked():
            self._widget.vehForm_3.toggle()
        if self._widget.vehForm_4.isChecked():
            self._widget.vehForm_4.toggle()
        if self._widget.vehForm_5.isChecked():
            self._widget.vehForm_5.toggle()

        if oneVeh == True:
            for veh in self.vehicles:
                if int(veh.rect.get_label()) == int(self.vehicle_id):
                    self.vehNames[(int(self.vehicle_id))] = str(self.tmpVehNames[(int(self.vehicle_id))])
                    print(self.vehNames)
                    veh.del_veh()
                    del self.vehicles[int(self.vehicles.index(veh))]
                    self.vehCounter = int(self.vehCounter) - 1
                    self.vehID[int(self.vehicle_id)] = int(self.vehicle_id)
                    print('Vehicles on the map:', self.vehCounter)

        if allVeh == True:

            for veh in self.vehicles:
                inx = int(veh.rect.get_label())
                self.vehID[int(inx)] = int(inx)
                self.vehNames[int(inx)] = str(self.tmpVehNames[int(inx)])
                veh.del_veh()
            self.vehCounter = 0
            del self.vehicles[:]
            self.set_limits()
            print('Vehicles on the map:', self.vehCounter)


        if self.vehCounter == 0:
            self._widget.delete_vehicle.setEnabled(False)

        if self.vehCounter < 5:
            self._widget.add_vehicle.setEnabled(True)

    def change_plain_text(self, message):
        self._widget.plainTextEdit.clear()
        self._widget.plainTextEdit.insertPlainText(message)

    def get_corr(self):

        inx=[]
        for i in range(0, len(self.vehicles)):
            inx.append(int(self.vehicles[i].rect.get_label()))

        for i in range(len(inx)):
            for j in range(len(inx)):
                self.x_shape[i*len(self.vehNames) + j] = self.vehicles[inx[j]].get_pos()[0] - self.vehicles[inx[i]].get_pos()[0]
                self.y_shape[i*len(self.vehNames) + j] = self.vehicles[inx[j]].get_pos()[1] - self.vehicles[inx[i]].get_pos()[1]
        print(inx)
        print(self.x_shape)
        print(self.y_shape)

    def set_limits(self):

        try:
            int(self._widget.xLim.text())
        except ValueError:
            self.change_plain_text('Wrong input! (expected int)')
        else:

            xLim = self._widget.xLim.text()
            yLim = self._widget.yLim.text()

            print('Limits are:', int(yLim), int(yLim))
            ax.set_xlim(0, int(xLim))
            ax.set_ylim(0, int(yLim))
            #ax.grid()
            self.figure.canvas.draw()
            self.figure.canvas.flush_events()

fig = plt.figure()

if __name__ == '__main__':
    fig.draw()
    rospy.spin()
