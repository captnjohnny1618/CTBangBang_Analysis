import sys
import os
from datetime import datetime

import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

import yaml # for reading ctbb_roi files

def pos_vector_convert(pos,size,direction):
    new_pos=[]
    
    if direction=='center->corner':
        for (p,s) in zip(pos,size):
            new_pos.append(p-s/2)
    elif direction=='corner->center':
        for (p,s) in zip(pos,size):
            new_pos.append(p+s/2)
    else:
        print("WARNING: Direction parameter must be 'center->corner' or 'corner->center'. Returning original position vector.")

    return new_pos
    

class roi:
    ## Properties
    # ROI
    roi_shape    = None # ellipse or rect to start
    slice_number = None
                           
    # Metadata             
    experiment_id = None
    date_added    = None
    last_modified = None
                           
    # GUI                  
    gui_roi_handle     = None
    gui_viewer_handle  = None
    gui_infobox_handle = None
                           
    # Backend              
    study_dirpath        = None
    image_stack_filepath = None
    output_filepath      = None

    ## Methods
    # Construction/Destruction 
    def __init__(self,study_dirpath,image_stack_filepath,roi_shape,viewer_obj,roi_info={}):
        self.study_dirpath=study_dirpath
        self.image_stack_filepath=image_stack_filepath
        self.gui_viewer_handle=viewer_obj

        # Translate from center coordinates to Qt position vector coordinates
        roi_info['position']=pos_vector_convert(roi_info['position'],roi_info['size'],'center->corner')
        
        # Instantiate ROI into GUI
        if roi_shape=='ellipse':
            self.gui_roi_handle=pg.EllipseROI(roi_info['position'],roi_info['size'],parent=viewer_obj.img_obj,removable=True)
            #self.gui_roi_handle=pg.EllipseROI(roi_info['position'],roi_info['size'],removable=True)
        elif (roi_shape=='rect') or (roi_shape=='rectangle'):
            self.gui_roi_handle=pg.RectROI(roi_info['position'],roi_info['size'],parent=viewer_obj.img_obj,removable=True)
            #self.gui_roi_handle=pg.RectROI(roi_info['position'],roi_info['size'],removable=True)
        else:
            print("ERROR: something went horribly wrong'")
            
        viewer_obj.plot_window.addItem(self.gui_roi_handle)
        
        # Map metadata into instance
        self.date_added=roi_info['date_added']
        self.last_modified=roi_info['last_modified']
        self.roi_shape=roi_shape
        self.slice_number=roi_info['slice']

        # Add textbox
        text="Name: {}\nPos: {}\nMean:{}".format("butts","more_butts","the most butts")
        self.gui_infobox_handle=pg.TextItem(text=text)
        self.gui_infobox_handle.show()
        print(dir(self.gui_infobox_handle))
        
        
        # Add callbacks
        self.gui_roi_handle.setAcceptedMouseButtons(QtCore.Qt.LeftButton)
        self.gui_roi_handle.sigClicked.connect(self.moved)
        self.gui_roi_handle.sigRegionChanged.connect(self.moved)
        self.gui_roi_handle.sigRemoveRequested.connect(self.remove)

        self.add_to_context_menu('Save ROI',self.save)


    @classmethod
    def ellipse(cls,viewer_obj):
        study_dirpath=viewer_obj.stack.study_dirpath
        image_stack_filepath=viewer_obj.stack.img_filepath
        roi_shape='ellipse'

        roi_info={}
        roi_info['slice']=[viewer_obj.stack.curr_image]
        roi_info['position']=[256,256]
        roi_info['size']=[32,32]
        roi_info['shape']=roi_shape
        roi_info['date_added']   =str(datetime.now())
        roi_info['last_modified']=str(datetime.now())
        
        return cls(study_dirpath,image_stack_filepath,roi_shape,viewer_obj,roi_info)

    @classmethod
    def rectangle(cls,viewer_obj):
        study_dirpath=viewer_obj.stack.study_dirpath
        image_stack_filepath=viewer_obj.stack.img_filepath
        roi_shape='rect'

        roi_info={}
        roi_info['slice']=[viewer_obj.stack.curr_image]
        roi_info['position']=[256,256]
        roi_info['size']=[32,32]
        roi_info['shape']=roi_shape
        roi_info['date_added']   =str(datetime.now())
        roi_info['last_modified']=str(datetime.now())

        return cls(study_dirpath,image_stack_filepath,roi_shape,viewer_obj,roi_info)

    @classmethod
    def fromfile(cls,roi_filepath,viewer_obj):
        # Parse argument inputs
        qi_raw_dir=os.path.dirname(roi_filepath)
        study_dirpath=os.path.dirname(qi_raw_dir)
        image_stack_filepath=viewer_obj.stack.img_filepath

        # Read raw data file
        with open(roi_filepath,'r') as f:
            roi_info=yaml.load(f)

        # Map over remaining metadata
        date_added=roi_info['date_added']
        last_modified=roi_info['last_modified']
        
        return cls(study_dirpath,image_stack_filepath,roi_info['shape'],viewer_obj,roi_info)

    def add_to_context_menu(self,menu_name,callback):
        menu=self.gui_roi_handle.getMenu();
        act = QtGui.QAction(menu_name, menu)
        act.triggered.connect(callback)
        menu.addAction(act)
        menu.remAct = act

    def __del__(self):
        pass

    # Callbacks
    def moved(self):
        self.last_modified=str(datetime.now())

    # Store/remove/validate methods
    def save(self):
        # Grab info about ROI
        (p,s)=self.get_position()
        stats=self.get_statistics()

        # Ask user for identifier
        items=("background","healthy_tissue","damaged_tissue","aorta")
        
        item, ok = QtGui.QInputDialog.getItem(self.gui_viewer_handle, "select input dialog", 
                                        "ROI Type", items, 0, False)

        if not ok:
            return
        
        # Collect ROI info into a dictionary
        save_dict={}
        save_dict['roi_name']      = item
        save_dict['shape']         = 'ellipse'
        save_dict['position']      = p
        save_dict['size']          = s
        save_dict['slice']         = self.slice_number
        save_dict['experiment_id'] = 'screening'
        save_dict['date_added']    = self.date_added
        save_dict['last_modified'] = self.last_modified

        save_dict['mean'] = stats['mean']
        save_dict['standard_dev']= stats['sd']
        save_dict['median'] = stats['median']
        save_dict['area'] = stats['area']

        roi_outfile=os.path.join(self.study_dirpath,'qi_raw',save_dict['roi_name']+'.ctbbroi')
        
        if os.path.exists(roi_outfile):

            def msgbtn(i):
                print("Button pressed is:",i.text())
                
            msg = QtGui.QMessageBox()
            msg.setIcon(QtGui.QMessageBox.Information)

            msg.setText("ROI already exists for current study. Overwrite?")
            msg.setWindowTitle("Replace existing ROI?")
            msg.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            msg.buttonClicked.connect(msgbtn)

            retval = msg.exec_()

            if retval==QtGui.QMessageBox.Ok:
                print("Saving ROI...")
                with open(roi_outfile,'w') as f:
                    yaml.dump(save_dict,f)
                print("Done.")
            else:
                print("ROI not saved")

    def remove(self):
        print("remove requested")
        
    def is_valid(self):
        pass

    def hide(self):
        self.gui_roi_handle.hide()

    def show(self):
        self.gui_roi_handle.show()

    # "Info" methods
    def get_statistics(self):
        stats={}
        stats['mean']=float(self.__get_mean__())
        stats['sd']=float(self.__get_sd__())
        stats['median']=self.__get_median__()
        stats['area']=self.__get_area__()
        return stats

    def __get_mean__(self):
        curr_slice=self.gui_viewer_handle.stack.curr_image
        data=self.gui_roi_handle.getArrayRegion(self.gui_viewer_handle.stack.stack[curr_slice,:,:],self.gui_viewer_handle.img_obj,axes=[0,1])
        return data.mean()

    def __get_sd__(self):
        curr_slice=self.gui_viewer_handle.stack.curr_image
        data=self.gui_roi_handle.getArrayRegion(self.gui_viewer_handle.stack.stack[curr_slice,:,:],self.gui_viewer_handle.img_obj,axes=[0,1])
        return data.std()

    def __get_median__(self):
        print()        

    def __get_area__(self):
        print()        
        
    def get_position(self):
        return (list(self.gui_roi_handle.pos()),list(self.gui_roi_handle.size()))
        

    def set_position(self,pos,size):
        new_pos=pos_vector_convert(pos,size,'center->corner')
        self.gui_roi_handle.setPos(new_pos)
        self.gui_roi_handle.setSize(size)
