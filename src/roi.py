import sys
import os

import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

import yaml # for reading ctbb_roi files

class roi:
    ## Properties
    # ROI
    roi_type=None # ellipse or rect to start
    
    # GUI
    gui_roi_handle=None
    gui_viewer_handle=None
    
    # Backend
    study_dirpath=None
    image_stack_filepath=None
    output_filepath=None

    ## Methods
    # Construction/Destruction 
    def __init__(self,study_dirpath,image_stack_filepath):
        self.study_dirpath=study_dirpath
        self.image_stack_filepath=image_stack_filepath
        pass

    @classmethod
    def frominteractive(cls,viewer_obj):
        study_dirpath=viewer_obj.stack.study_dirpath
        image_stack_filepath=viewer_obj.stack.img_filepath
        test=pg.EllipseROI([256,256],[32,32],parent=viewer_obj.img_obj)
        
        return cls(study_dirpath,image_stack_filepath)

#    @classmethod
#    def fromfile(cls,roi_filepath):
#        qi_raw_dir=os.path.dirname(roi_filepath)
#        study_dirpath=os.path.dirname(qi_raw_dir)
#        image_stack_filepath=viewer_obj.img_obj.img_filepath
#        return cls(study_dirpath,image_stack_filepath)

    def __del__(self):
        pass

    # Store/remove/validate methods
    def save(self):
        pass

    def remove(self):
        pass
        
    def is_valid(self):
        pass

    # "Info" methods
    def get_statistics(self):
        stats={}
        stats['mean']=self.__get_mean__()
        stats['median']=self.__get_median__()
        stats['area']=self.__get_area__()
        return stats

    def __get_mean(self):
        pass
    def __get_median__(self):
        pass
    def __get_area__(self):
        pass
        
    def get_position(self):
        pass

    def set_position(self):
        pass

    
