import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons
import nibabel as nib
import numpy as np
import time
import math
import SimpleITK as sitk
import os


class qualityChecker:
    def __init__(self, img):
        self.axarr0Click = False
        self.axarr1Click = False
        self.axarr2Click = False

        sitk_t1 = sitk.ReadImage(img)
        self.img = sitk.GetArrayFromImage(sitk_t1)

        self.AXIS2 = self.img.shape[-1]
        self.AXIS0 = self.img.shape[-2]
        self.AXIS1 = self.img.shape[-3]

        self.DIRECTION = 0

        self.f, self.axarr = plt.subplots(1, 3, figsize=(10,5))
        self.f.canvas.manager.set_window_title(os.path.basename(img)) 
        self.f.suptitle("B"+str(self.DIRECTION)+" Image", fontsize=15, fontweight="bold")
        self.axarr[1].set_title("Coronal", fontsize=12)
        self.axarr[0].set_title("Axial", fontsize=12)
        self.axarr[2].set_title("Saggital", fontsize=12)


        self.CURRENT1 = round(self.AXIS1/2)
        self.CURRENT0 = round(self.AXIS0/2)
        self.CURRENT2 = round(self.AXIS2/2)
        
        self.axarr[1].set_xlabel(str(self.CURRENT1)+"/"+str(self.AXIS1))
        self.axarr[0].set_xlabel(str(self.CURRENT0)+"/"+str(self.AXIS0))
        self.axarr[2].set_xlabel(str(self.CURRENT2)+"/"+str(self.AXIS2))

        self.img0 = self.axarr[0].imshow(self.img[self.DIRECTION,:,self.CURRENT0,:], cmap='gray')
        self.img1 = self.axarr[1].imshow(self.img[self.DIRECTION, self.CURRENT1,:,:], cmap='gray')
        self.img2 = self.axarr[2].imshow(self.img[self.DIRECTION,:,:,self.CURRENT2], cmap='gray')

        self.axprev = self.f.add_axes([0.7, 0.05, 0.1, 0.075])
        self.axnext = self.f.add_axes([0.81, 0.05, 0.1, 0.075])
        self.axfinish = self.f.add_axes([0.05, 0.05, 0.1, 0.075])
        #self.ax_elim = self.f.add_axes([0.412, 0.85, 0.2, 0.04])
        self.ax_check = self.f.add_axes([0.01, 0.75, 0.15, 0.2])

        self.ax0background = self.f.canvas.copy_from_bbox(self.axarr[0].bbox)
        self.axbackground = self.f.canvas.copy_from_bbox(self.axarr[1].bbox)
        self.ax2background = self.f.canvas.copy_from_bbox(self.axarr[2].bbox)

        self.eliminate = None
        self.check_status = []
        self.b_images = []
        self.vis = []
        for x in range(0, self.img.shape[0]):
            self.b_images.append("b"+str(x))
            self.vis.append(True)

        self.directions = {}

        for b in self.b_images:
            self.directions[str(b)] = True

        self.ax_check.set_visible(False)

        self.check = CheckButtons(self.ax_check, ["Keep Direction"], [True])
        self.check.on_clicked(self.func)

    def onclick_select(self, event):
        if event.inaxes == self.axarr[1]:
            if self.axarr1Click:
                self.axarr1Click = False
            else:
                self.axarr1Click = True
                self.axarr0Click = False
                self.axarr2Click = False
        elif event.inaxes == self.axarr[0]:
            if self.axarr0Click:
                self.axarr0Click = False
            else:
                self.axarr0Click = True
                self.axarr1Click = False
                self.axarr2Click = False
        elif event.inaxes == self.axarr[2]:
            if self.axarr2Click:
                self.axarr2Click = False
            else:
                self.axarr2Click = True
                self.axarr0Click = False
                self.axarr1Click = False
        elif event.inaxes == self.axnext:
            if self.DIRECTION < (self.img.shape[0]-1):
                self.DIRECTION +=1
                self.img0.set_data(self.img[self.DIRECTION, :,self.CURRENT0,:])
                self.img1.set_data(self.img[self.DIRECTION,self.CURRENT1, :, :])
                self.img2.set_data(self.img[self.DIRECTION,:,:,self.CURRENT2])
                self.f.suptitle("B"+str(self.DIRECTION)+" Image", fontsize=15, fontweight="bold")
                #print(self.directions["b"+str(self.DIRECTION)])
                if self.directions["b"+str(self.DIRECTION)] and not self.check.lines[0][0].get_visible():
                    self.check.set_active(0)

                if not self.directions["b"+str(self.DIRECTION)] and self.check.lines[0][0].get_visible():
                    self.check.set_active(0)

                if self.DIRECTION != 0:
                    self.ax_check.set_visible(True)
                else:
                    self.ax_check.set_visible(False)

                self.f.canvas.draw_idle()

        elif event.inaxes == self.axprev:
            if self.DIRECTION > 0:
                self.DIRECTION -=1
                self.img0.set_data(self.img[self.DIRECTION, :,self.CURRENT0,:])
                self.img1.set_data(self.img[self.DIRECTION,self.CURRENT1, :, :])
                self.img2.set_data(self.img[self.DIRECTION,:,:,self.CURRENT2])
                self.f.suptitle("B"+str(self.DIRECTION)+" Image", fontsize=15, fontweight="bold")
                
                if self.directions["b"+str(self.DIRECTION)] and not self.check.lines[0][0].get_visible():
                    self.check.set_active(0)

                if not self.directions["b"+str(self.DIRECTION)] and self.check.lines[0][0].get_visible():
                    self.check.set_active(0)

                if self.DIRECTION != 0:
                    self.ax_check.set_visible(True)
                else:
                    self.ax_check.set_visible(False)

                self.f.canvas.draw_idle()

        elif event.inaxes == self.axfinish:
            plt.close()

    def func(self,label):
        if self.check.lines[0][0].get_visible():
            self.directions["b"+str(self.DIRECTION)] = True
        else:
            self.directions["b"+str(self.DIRECTION)] = False

    def mouse_move(self, event):
        if event.inaxes == self.axarr[1]:
            if self.axarr1Click:
                x, y = round(event.xdata), round(event.ydata)
                if x > self.img.shape[-2]:
                    x = self.img.shape[-2]
                if y > self.img.shape[-1]:
                    y = self.img.shape[-1]
                self.img0.set_data(self.img[self.DIRECTION,:,x,:])
                self.img2.set_data(self.img[self.DIRECTION,:,:,y])

                self.axarr[0].set_xlabel(str(x)+"/"+str(self.AXIS0))
                self.axarr[2].set_xlabel(str(y)+"/"+str(self.AXIS2))
                self.CURRENT0 = x
                self.CURRENT2 = y
                self.f.canvas.draw_idle()
                self.f.canvas.flush_events()
                plt.pause(0.000001)
        elif event.inaxes == self.axarr[0]:
            if self.axarr0Click:
                x, y = round(event.xdata), round(event.ydata)
                if x > self.img.shape[-1]:
                    x = self.img.shape[-1]
                if y > self.img.shape[1]:
                    y = self.img.shape[1]

                self.img1.set_data(self.img[self.DIRECTION,y,:,:])
                self.img2.set_data(self.img[self.DIRECTION,:,:,x])
                self.axarr[1].set_xlabel(str(y)+"/"+str(self.AXIS1))
                self.axarr[2].set_xlabel(str(x)+"/"+str(self.AXIS2))
                self.CURRENT1 = y
                self.CURRENT2 = x
                self.f.canvas.draw_idle()
                self.f.canvas.flush_events()
                plt.pause(0.000001)
        elif event.inaxes == self.axarr[2]:
            if self.axarr2Click:
                x, y = round(event.xdata), round(event.ydata)
                if x > self.img.shape[-2]:
                    x = self.img.shape[-2]
                if y > self.img.shape[1]:
                    y = self.img.shape[1]
                self.img0.set_data(self.img[self.DIRECTION,:,x,:])
                self.img1.set_data(self.img[self.DIRECTION,y,:,:])
                self.axarr[0].set_xlabel(str(x)+"/"+str(self.AXIS0))
                self.axarr[1].set_xlabel(str(y)+"/"+str(self.AXIS1))
                self.CURRENT0 = x
                self.CURRENT1 = y
                self.f.canvas.draw_idle()
                self.f.canvas.flush_events()
                plt.pause(0.000001)

    def run(self):

        bnext = Button(self.axnext, 'Next')

        bprev = Button(self.axprev, 'Previous')

        finish = Button(self.axfinish, "Finish")

        directions = self.img.shape[0]
        
        self.f.canvas.mpl_connect("button_press_event",self.onclick_select)
        self.f.canvas.mpl_connect("motion_notify_event",self.mouse_move)

        plt.show()