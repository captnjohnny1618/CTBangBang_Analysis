#!/usr/bin/env python
import os
import sys
import time
import yaml

import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

from argparse import ArgumentParser

from roi import roi

def load_prm(prm_filepath):
    # Clean up the file and then load
    with open(prm_filepath,'r') as f:
        data=f.read()
        data=data.replace("\t"," ")
        data=data.replace("\%","#")
        prm_dict=yaml.load(data)

    return prm_dict

class image_stack:
    stack=None
    curr_image=0
    n_images=None
    width=512
    height=512
    study_dirpath=None
    img_filepath=None
    prm_filepath=None
    
    prm_dict=None

    #python3 ~/Code/CTBangBang_Pipeline_Analysis/src/view.py /Fast_Storage/RSNA_2017/library/recon/100/15fb037a6279308801f10570c5f3f2c1_k2_st0.6/w

    def __init__(self,study_dirpath,width,height,offset):
        print('offset: ' + str(offset));
        print('width: ' +  str(width ));
        print('height: ' + str(height));

        self.width=width;
        self.height=height;

        # Set up paths to files
        self.study_dirpath=os.path.abspath(study_dirpath)

        fileparts=os.path.basename(self.study_dirpath)
        fileparts=fileparts.split("_")
        pipeline_id=fileparts[0]
        kernel=fileparts[1]
        slice_thickness=fileparts[2]
        dose=os.path.basename(os.path.dirname(self.study_dirpath))
        
        self.img_filepath=os.path.join(self.study_dirpath,'img',"_".join([pipeline_id,'d'+dose,kernel,slice_thickness])+'.img')
        self.prm_filepath=os.path.join(self.study_dirpath,'img',"_".join([pipeline_id,'d'+dose,kernel,slice_thickness])+'.prm')

        # Grab parameter file
        self.prm_dict=load_prm(self.prm_filepath)

        # Read in image stack a prep for display
        with open(self.img_filepath,'r') as f:

            f.seek(offset,os.SEEK_SET);
            self.stack=np.fromfile(f,'float32')

        n_slices=self.stack.size/(self.width*self.height)

        self.stack=self.stack.reshape(int(n_slices),self.width,self.height);
        self.stack=1000*(self.stack-0.01923)/(0.01923)
        stack_size=self.stack.shape
        self.n_images=stack_size[0];

    def __getitem__(self,key):
        if (key in range(0,self.n_images)):
            return self.stack[key,:,:]
        else:
            raise IndexError

    def next_image(self):
        self.curr_image=min(self.curr_image+1,self.n_images-1);

    def prev_image(self):
        self.curr_image=max(self.curr_image-1,0);

class viewer(pg.GraphicsLayoutWidget):
    #objects
    app=None;
    stack=None;
    plot_window=None;
    img_obj=None;
    hist_obj=None;
    rois=[]

    window=1600;
    level=-600;
    
    is_windowing=False;
    is_playing=False;
    
    def __init__(self,app,stack):
        super(viewer,self).__init__()
        self.app=app
        self.stack=stack;
        self.initUI()
        self.load_saved_rois()
        self.update_image()

    def initUI(self):
        self.setWindowTitle('CTBB Image Viewer');        
        self.plot_window=self.addViewBox()
        #self.plot_window = self.addPlot()
        ##
        #self.plot_window.hideAxis('left');
        #self.plot_window.hideAxis('bottom');
        self.plot_window.invertY();
        #self.plot_window.invertX();
        #
        self.img_obj = pg.ImageItem()
        self.img_obj.setParent(self.plot_window)
        #
        self.img_obj.aspectLocked=True;
        self.plot_window.addItem(self.img_obj)

        self.img_obj.setImage(self.stack[0],levels=(self.level-self.window/2,self.level+self.window/2))

        self.resize(512, 512)
        self.img_obj.show()
        self.show()

    def load_saved_rois(self):
        roi_dir=os.path.join(self.stack.study_dirpath,'qi_raw')
        files=os.listdir(roi_dir)
        for f in files:
            if os.path.splitext(f)[1]=='.ctbbroi':
                self.rois.append(roi.fromfile(os.path.join(roi_dir,f),self))

    def update_image(self):
        # Handle image data
        self.img_obj.setImage(self.stack[self.stack.curr_image],levels=(self.level-self.window/2,self.level+self.window/2))
        self.app.processEvents()

        # Set ROI visibility
        for r in self.rois:
            if r.slice_number[0]==self.stack.curr_image:
                r.show()
                #r.gui_roi_handle.show()
            else:
                r.hide()
                #r.gui_roi_handle.hide()

    def play(self):
        while self.is_playing and self.stack.curr_image<=self.stack.n_images-1:
            self.stack.next_image();
            time.sleep(0.041);
            self.update_image();

    def rewind(self):
        while self.is_playing and self.stack.curr_image>=0:
            self.stack.prev_image();
            time.sleep(0.041);
            self.update_image();

    def keyPressEvent(self,e):
        if e.matches(QtGui.QKeySequence.Close):
            sys.exit()
        elif (e.key()==QtCore.Qt.Key_Right) | (e.key()==QtCore.Qt.Key_F):
            self.stack.next_image()
        elif (e.key()==QtCore.Qt.Key_Left) | (e.key()==QtCore.Qt.Key_B):
            self.stack.prev_image()
        elif e.key()==QtCore.Qt.Key_Space and e.modifiers()==QtCore.Qt.NoModifier:
            self.is_playing=not self.is_playing
            self.play();
        elif e.key()==QtCore.Qt.Key_Space and e.modifiers()!=QtCore.Qt.NoModifier:
            self.is_playing=not self.is_playing
            self.rewind();            
        elif e.key()==QtCore.Qt.Key_W:
            self.set_wl()
        elif e.key()==QtCore.Qt.Key_R:
            self.add_roi()
        else:
            pass

        self.update_image();

    def set_wl(self):        
        self.is_windowing=not self.is_windowing;

        if self.is_windowing:
            self.hist_obj = pg.HistogramLUTItem()
            self.hist_obj.setImageItem(self.img_obj)
            self.addItem(self.hist_obj);
        else:
            self.window=self.img_obj.levels[1]-self.img_obj.levels[0]
            self.level=(self.img_obj.levels[1]+self.img_obj.levels[0])/2
            self.removeItem(self.hist_obj);

    def add_roi(self):
        self.rois.append(roi.ellipse(self))

    def hide_show_roi(self):
        if self.shown:
            self.rois[0].gui_roi_handle.hide()
        else:
            self.rois[0].gui_roi_handle.show()

        self.shown=1-self.shown
 
def main():
    app=QtGui.QApplication(sys.argv)

    parser = ArgumentParser(description="")
    parser.add_argument('study_dirpath', help='Path to float binary to be read');
    parser.add_argument('width' , nargs='?', default=512,  help='Width of the image stack being read');  #required=False,
    parser.add_argument('height', nargs='?', default=512,  help='Height of the image stack being read'); #required=False,
    parser.add_argument('offset', nargs='?', default=0,  help='Height of the image stack being read'); #required=False,
    args=parser.parse_args()

    study_dirpath=args.study_dirpath;
    if study_dirpath[len(study_dirpath)-1]==os.sep:
        study_dirpath=os.path.dirname(study_dirpath)

    width= int(args.width);
    height=int(args.height);
    offset=int(args.offset);
    
    v=viewer(app,image_stack(study_dirpath,width,height,offset))

    #if len(sys.argv)==2:
    #    v=viewer(app,study_dirpath,width,height)
    #else:
    #    v=viewer(app,sys.argv[1],sys.argv[2],sys.argv[3]);
    sys.exit(app.exec_())

if __name__=="__main__":
    main();
      
        
  
