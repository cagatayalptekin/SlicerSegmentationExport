import logging
import numpy as np
import os
from typing import Annotated, Optional
import sys
import qt
from qt import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog
import time
from time import sleep
import vtk
import shutil 
import os.path
import vtkITK
from slicer.util import getNode
import ScreenCapture
import slicer
import shutil
import zipfile
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)
from slicer import vtkMRMLSegmentationNode
from slicer import vtkMRMLScalarVolumeNode
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersCore import vtkTubeFilter
from vtkmodules.vtkFiltersSources import vtkLineSource
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)


#
# SlicerSegmentationExport
#


class SlicerSegmentationExport(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("SlicerSegmentationExport")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Cagatay Alptekin (Non-Nocere)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/cagatayalptekin/SlicerSegmentationExport">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Cagatay Alptekin, Non-Nocere.
""")

        # Additional initialization step after application startup is complete
 

@parameterNodeWrapper
class SlicerSegmentationExportParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    minimumThreshold - The minimum threshold value for segmenting anatomical model.
    maximumThreshold - The maximum threshold value for segmenting anatomical model. 
    segmentationNode - To access any type of segmentation node from all of the data such as paint and node and also used for calculating slice offset values(starting and ending slice points)..
    checkCalculationRed10 - To check for creating keyboard bindings happens just one time for red slices.
    checkCalculationGreen10 - To check for creating keyboard bindings happens just one time for green slices.
    checkCalculationYellow10 - To check for creating keyboard bindings happens just one time for yellow slices.
    red_slice - To check for if red slice will be selected for screen capture.
    green_slice - To check for if green slice will be selected for screen capture.
    yellow_slice - To check for if yellow slice will be selected for screen capture.
    SSPaintInclude - To check for if paint brushes will be added to slices or not.
    lineLength - To give line a specific length.
    checkUndo - To check for creating keyboard bindings happens just one time for undo/redo operation.
    imageNumber - To identify a number for how many screen capture images will be taken.
    path - Path for saving screen capture images.
    pathforbone - Path for bone segmentation exporting.
    pathforcaliber - Path for caliber exporting.
    pathforline - Path for line exporting.
    pathforsavescene - Path for saving the whoole scene at any point in slicer.    
    greenMiddleOffset - Green offset value that is at the middle,it is received when the dicom data first loaded   
    yellowMiddleOffset - Green offset value that is at the middle,it is received when the dicom data first loaded
    linenames: list[str] - To save line names to prevent creating lines with same name.
    num:int=0 - When name of the line is not specified, it generates lines, according to their number. It is incremented every time.
    x:int=50 - X coordinate to generate line when coordinates are not specified by user.
    y:int=50 - Y coordinate to generate line when coordinates are not specified by user.
    z:int=-100 - Z coordinate to generate line when coordinates are not specified by user.

    """

    inputVolume: vtkMRMLScalarVolumeNode     
    
    minimumThreshold: Annotated[float, WithinRange(-500, 3000)] = 170
    maximumThreshold: Annotated[float, WithinRange(-500, 3000)] = 1500
    segmentationNode: vtkMRMLSegmentationNode
    checkCalculationRed10:int=0     
    checkCalculationGreen10:int=0    
    checkCalculationYellow10:int=0
    red_slice:bool=False
    green_slice:bool=False
    yellow_slice:bool=False
    SSPaintInclude:bool=False
    lineLength: Annotated[float, WithinRange(0, 300)] = 50
    checkUndo:int=0   
    imageNumber:Annotated[float, WithinRange(0, 1000)] = 100
    path:str=""
    pathforbone:str=""
    pathforcaliber:str=""
    pathforline:str=""
    pathforsavescene:str=""
    redMiddleOffset:float
    greenMiddleOffset:float
    yellowMiddleOffset:float
    linenames: list[str] = []
    num:int=0
    x:int=50
    y:int=50
    z:int=-100




#
# SlicerSegmentationExportWidget
#


class SlicerSegmentationExportWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)
        
        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/SlicerSegmentationExport.ui"))
        

        
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)
     
        moduleDir = os.path.dirname(slicer.util.modulePath(self.__module__))
        
        #Icons for buttons
        iconPathErase = os.path.join(moduleDir, 'Resources/Icons', 'erase.png')
        iconPathDeselect = os.path.join(moduleDir, 'Resources/Icons', 'deselect.jpg')
        iconPathUndo = os.path.join(moduleDir, 'Resources/Icons', 'undo.png')
        iconPathRedo = os.path.join(moduleDir, 'Resources/Icons', 'redo.png')
        iconPathRemoveCalibers= os.path.join(moduleDir, 'Resources/Icons', 'x-mark.png')
        iconErase = qt.QIcon(iconPathErase)
        iconDeselect = qt.QIcon(iconPathDeselect)
        iconUndo = qt.QIcon(iconPathUndo)
        iconRedo = qt.QIcon(iconPathRedo)
        iconRemoveCalibers=qt.QIcon(iconPathRemoveCalibers)
        self.ui.erase.setIcon(iconErase)
        self.ui.removepaintcursor.setIcon(iconDeselect)
        self.ui.undo.setIcon(iconUndo)
        self.ui.redo.setIcon(iconRedo)
        self.ui.removecalibers.setIcon(iconRemoveCalibers)
        


        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = SlicerSegmentationExportLogic()
        self.helper=SlicerHelper()
        

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Connecting buttons
        self.ui.removecalibers.connect("clicked(bool)", self.removeCalibers)
        self.ui.together.connect("clicked(bool)", self.together)
        self.ui.createCalibersAtCorners.connect("clicked(bool)", self.createCalibersAtCorners)
        self.ui.checkbox_red.connect("clicked(bool)", self.toggleCheckboxRed)
        self.ui.checkbox_green.connect("clicked(bool)", self.toggleCheckboxGreen)
        self.ui.checkbox_yellow.connect("clicked(bool)", self.toggleCheckboxYellow)
        self.ui.checkbox_red2.connect("clicked(bool)", self.toggleCheckboxRed)
        self.ui.checkbox_green2.connect("clicked(bool)", self.toggleCheckboxGreen)
        self.ui.checkbox_yellow2.connect("clicked(bool)", self.toggleCheckboxYellow)
        self.ui.withpaint.connect("clicked(bool)", self.toggleSSPaintInclude)
        self.ui.withpaint2.connect("clicked(bool)", self.toggleSSPaintInclude)
        self.ui.startsegmentation.connect("clicked(bool)", self.startSegmentation)
        self.ui.selectfolder.connect("clicked(bool)", self.selectFolder)
        self.ui.selectfolderforsavescene.connect("clicked(bool)", self.selectFolderForSaveScene)
        self.ui.selectfolderforbone.connect("clicked(bool)", self.selectFolderForBone)
        self.ui.selectfolderforcaliber.connect("clicked(bool)", self.selectFolderForcaliber)
        self.ui.selectfolder2.connect("clicked(bool)", self.selectFolder)
        self.ui.selectfolderforsavescene2.connect("clicked(bool)", self.selectFolderForSaveScene)
        self.ui.selectfolderforbone2.connect("clicked(bool)", self.selectFolderForBone)
        self.ui.selectfolderforcaliber2.connect("clicked(bool)", self.selectFolderForcaliber)
        self.ui.selectfolderforline.connect("clicked(bool)", self.selectFolderForLine)
        self.ui.selectfolderforline2.connect("clicked(bool)", self.selectFolderForLine)
        self.ui.selectredpaint10.connect("clicked(bool)", self.selectRedPaint10)
        self.ui.selectredpaint20.connect("clicked(bool)", self.selectRedPaint20)
        self.ui.selectgreenpaint10.connect("clicked(bool)", self.selectGreenPaint10)
        self.ui.selectgreenpaint20.connect("clicked(bool)", self.selectGreenPaint20)
        self.ui.selectyellowpaint10.connect("clicked(bool)", self.selectYellowPaint10)
        self.ui.selectyellowpaint20.connect("clicked(bool)", self.selectYellowPaint20)
        self.ui.generateline.connect("clicked(bool)", self.generateLine)
        self.ui.deleteline.connect("clicked(bool)", self.deleteLine)
        self.ui.erase.connect("clicked(bool)", self.Erase)
        self.ui.removepaintcursor.connect("clicked(bool)", self.removepaintcursor)
        self.ui.exportbonebutton.connect("clicked(bool)", self.exportBone)
        self.ui.exportcaliberbutton.connect("clicked(bool)", self.exportPaint)
        self.ui.undo.connect("clicked(bool)", self.logic.undo)
        self.ui.redo.connect("clicked(bool)", self.logic.redo)
        self.ui.exportimages.connect("clicked(bool)", self.exportImages)
        self.ui.zipfoldersforimages.connect("clicked(bool)", self.zipImages)
        self.ui.savescene.connect("clicked(bool)", self.saveScene)
        

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()





        sliceNode=self.getSliceNode("Red")
        sliceOffset=sliceNode.GetSliceOffset()
        print('red middle offset')
        print(sliceOffset)
        self._parameterNode.redMiddleOffset=sliceOffset
        sliceNode=self.getSliceNode("Green")
        sliceOffset=sliceNode.GetSliceOffset()
        print('green middle offset')
        print(sliceOffset)
        self._parameterNode.greenMiddleOffset=sliceOffset
        sliceNode=self.getSliceNode("Yellow")
        sliceOffset=sliceNode.GetSliceOffset()
        print('yellow middle offset')
        print(sliceOffset)
        self._parameterNode.yellowMiddleOffset=sliceOffset







    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()
        
        
        
        # Resetting the scene while entering the scene so that any added objects will be seen directly
        layoutManager = slicer.app.layoutManager()
        threeDWidget = layoutManager.threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        threeDView.rotateToViewAxis(3)  # look from anterior direction
        threeDView.resetFocalPoint()  # reset the 3D view cube size and center it
        threeDView.resetCamera()  # reset camera zoom
 
        
       # Connecting undo/redo operation with keyboard
        shortcutKeys=["Ctrl+z","Ctrl+y"]
        checkUndo=self._parameterNode.checkUndo
        self.helper.setupShortcuts(-1,checkUndo, shortcutKeys, 0, 0, 0,'redo')
        
    
        # Ensuring it happens only one time
        self._parameterNode.checkUndo=self._parameterNode.checkUndo+1







 
    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

        # Getting middle offsets of slices to calculate first and last slice offsets for image capturing.




    def setParameterNode(self, inputParameterNode: Optional[SlicerSegmentationExportParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
    
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:
        if self._parameterNode and self._parameterNode.inputVolume:
            
            # Add tooltips to buttons 
            self.ui.removecalibers.toolTip = _("Remove all of the calibers from scene")
 
            


         
    # Remove all of the paint brushes from scene.
    def removeCalibers(self):

        paintNode = slicer.mrmlScene.GetFirstNodeByName("paint-node")
        slicer.mrmlScene.RemoveNode(paintNode)
    # Save the whole slicer scene
    def saveScene(self):
        path=self._parameterNode.pathforsavescene
         
        sceneSaveFilename = path + "/" + time.strftime("%Y%m%d-%H%M%S") + ".mrb"


        # Save scene
        if path =="":
            print("Please give a valid path to save scene!")
        else:
        
            if slicer.util.saveScene(sceneSaveFilename):
              print("Scene saved to: {0}".format(sceneSaveFilename))
            else:
              print("Scene saving failed")
              
              
    # Zip the folder containing slice images
    def zipImages(self):
            
        self.logic.zipImages(self._parameterNode.path)
    
    
    # Export desired slice images according to image number and image path
    def exportImages(self):
        self._parameterNode.imageNumber=self.ui.imageNumber.value

        self.logic.exportImages(self._parameterNode.path,self._parameterNode.imageNumber,self._parameterNode.green_slice,self._parameterNode.red_slice,self._parameterNode.yellow_slice,self._parameterNode.SSPaintInclude,self._parameterNode.redMiddleOffset,self._parameterNode.greenMiddleOffset,self._parameterNode.yellowMiddleOffset)


    
        
        
    # Export bone from the model with given values 
    def exportBone(self):
        self._parameterNode.minimumThreshold=self.ui.minimumThreshold.value
        self._parameterNode.maximumThreshold=self.ui.maximumThreshold.value
        
        self._parameterNode.imageNumber=self.ui.imageNumber.value
        if self._parameterNode.maximumThreshold>self._parameterNode.minimumThreshold:

            self.logic.startSegmentation(self._parameterNode.minimumThreshold,self._parameterNode.maximumThreshold,1,self._parameterNode.pathforbone)
        else:
            print('Minimum threshold must be smaller than the maximum threshold')
    # Export caliber oobjects from the 3d view
    def exportPaint(self):
        self.logic.exportPaint(self._parameterNode.pathforcaliber)
        
        
    # Switch paint brush with standard cursor pointer
    def removepaintcursor(self):
        segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
        segmentEditorWidget.setActiveEffectByName("")
        slicer.app.processEvents()
    def together(self):
        self.createCalibersAtCorners()
        self.exportImages()
        
        self.exportPaint()
        self.exportBone()
        self.generateLine()
        self.saveScene()
        
    # Control the red slice checkbox for including red slice to exporting images
    def toggleCheckboxRed(self):
        self._parameterNode.red_slice=not self._parameterNode.red_slice
    # Control the green slice checkbox for including green slice to exporting images
    def toggleCheckboxGreen(self):
        self._parameterNode.green_slice=not self._parameterNode.green_slice
    # Control the yellow slice checkbox for including yellow slice to exporting images
    def toggleCheckboxYellow(self):
        self._parameterNode.yellow_slice=not self._parameterNode.yellow_slice
    # Check for including paint brushes to exporting images
    def toggleSSPaintInclude(self):
        self._parameterNode.SSPaintInclude=not self._parameterNode.SSPaintInclude
        
    # Information about anatomical plane that is being painted 
    def getSliceNode(self, color):
        lm = slicer.app.layoutManager()
        sliceWidget = lm.sliceWidget(color)
        sliceLogic = sliceWidget.sliceLogic()
        sliceNode = sliceLogic.GetSliceNode()
        return sliceNode
        
    # Generate line based on given length
    def generateLine(self)->None:
        coordinates = self.ui.coordinatesofline.toPlainText().split(',') 
        print(coordinates[0])
        if coordinates[0] !='':
           self._parameterNode.x, self._parameterNode.y, self._parameterNode.z = map(int, coordinates)
        else:
            self._parameterNode.x+=5
            self._parameterNode.y+=5
            self._parameterNode.z+=5
        linenames=self._parameterNode.linenames
        linename=self.ui.nameofline.toPlainText()
        self._parameterNode.num+=1
            
        
       
        self.logic.generateLine(self.ui.lineLengthSliderWidget.value, self._parameterNode.x, self._parameterNode.y, self._parameterNode.z,self._parameterNode.pathforline,linename,linenames,self._parameterNode.num)
    # Delete line from given name
    def deleteLine(self)->None:
        name = self.ui.linetobedeleted.toPlainText()

        # Check if the name is empty
        if name == '':
            # If linenames is not empty, use the last linename
            if self._parameterNode.linenames:
                name = self._parameterNode.linenames[-1]
                self.logic.deleteLine(name)
                self._parameterNode.linenames.remove(name)
            else:
                # Handle case where there are no linenames
                print("No lines available to delete.")
                return  # Or any other handling you'd like
        else:
            check=0
            for item in self._parameterNode.linenames:
                if item==name:
                    check+=1
            if check==0:
                print('There is no line with the name->'+name)
            else:
                self.logic.deleteLine(name)
                self._parameterNode.linenames.remove(name)

        # Now delete the line

       

    
    
        # Check baselinevolume not coming null, and if so return it.
    def getBaselineVolume(self):
        try:
            self._parameterNode.segmentationNode = getNode('paint-node')
                     
        except slicer.util.MRMLNodeNotFoundException:
            self._parameterNode.segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode","paint-node")

    
        baselineVolume = self._parameterNode.inputVolume
        return baselineVolume
    
    # Selection of painting buttons according to their size and anatomical plane(axial(red),coronal(green),sagittal(yellow))
    def createCalibersAtCorners(self):
        baselineVolume=self.getBaselineVolume()
        self.logic.createCaliberAtCorners(self._parameterNode.segmentationNode,baselineVolume)
    def selectRedPaint10(self):

        baselineVolume=self.getBaselineVolume()

        sliceNode=self.getSliceNode("Red")
           
        self.logic.selectPaint(baselineVolume,10.0,'red',sliceNode,self._parameterNode.checkCalculationRed10,self._parameterNode.segmentationNode,self._parameterNode.redMiddleOffset,self._parameterNode.greenMiddleOffset,self._parameterNode.yellowMiddleOffset)
        
        self._parameterNode.checkCalculationRed10+=1
         
    def selectRedPaint20(self):
        baselineVolume=self.getBaselineVolume()

        sliceNode=self.getSliceNode("Red")
      
        self.logic.selectPaint(baselineVolume ,20.0,'red',sliceNode,self._parameterNode.checkCalculationRed10,self._parameterNode.segmentationNode,self._parameterNode.redMiddleOffset,self._parameterNode.greenMiddleOffset,self._parameterNode.yellowMiddleOffset)
        
        self._parameterNode.checkCalculationRed10+=1
    def selectGreenPaint10(self):
        baselineVolume=self.getBaselineVolume()

        sliceNode=self.getSliceNode("Green")
             
        self.logic.selectPaint(baselineVolume ,10.0,'green',sliceNode,self._parameterNode.checkCalculationGreen10,self._parameterNode.segmentationNode,self._parameterNode.redMiddleOffset,self._parameterNode.greenMiddleOffset,self._parameterNode.yellowMiddleOffset)
        
        self._parameterNode.checkCalculationGreen10+=1
    
    def selectGreenPaint20(self):
        baselineVolume=self.getBaselineVolume()
        
        sliceNode=self.getSliceNode("Green")       
     
        self.logic.selectPaint(baselineVolume ,20.0,'green',sliceNode,self._parameterNode.checkCalculationGreen10,self._parameterNode.segmentationNode,self._parameterNode.redMiddleOffset,self._parameterNode.greenMiddleOffset,self._parameterNode.yellowMiddleOffset)
        
        self._parameterNode.checkCalculationGreen10+=1
    def selectYellowPaint10(self):
        baselineVolume=self.getBaselineVolume()
        
        sliceNode=self.getSliceNode("Yellow")
       
        self.logic.selectPaint(baselineVolume ,10.0,'yellow' ,sliceNode,self._parameterNode.checkCalculationYellow10,self._parameterNode.segmentationNode,self._parameterNode.redMiddleOffset,self._parameterNode.greenMiddleOffset,self._parameterNode.yellowMiddleOffset)
       
        self._parameterNode.checkCalculationYellow10+=1
        
    def selectYellowPaint20(self,baselineVolume):
        baselineVolume=self.getBaselineVolume()

        sliceNode=self.getSliceNode("Yellow")
        
        self.logic.selectPaint(baselineVolume, 20.0,'yellow' ,sliceNode,self._parameterNode.checkCalculationYellow10,self._parameterNode.segmentationNode,self._parameterNode.redMiddleOffset,self._parameterNode.greenMiddleOffset,self._parameterNode.yellowMiddleOffset)

        self._parameterNode.checkCalculationYellow10+=1
        
    # Erase painting brushes
    def Erase(self):
        self.logic.Erase()
        
    # Selecting folders for specific operations
    def selectFolderForSaveScene(self):
        self.helper.selectFolder('save-scene',self.ui,self._parameterNode)

    def selectFolderForcaliber(self):
        self.helper.selectFolder('caliber',self.ui,self._parameterNode)
    def selectFolderForLine(self):
        self.helper.selectFolder('line',self.ui,self._parameterNode)

    def selectFolderForBone(self):
        self.helper.selectFolder('bone',self.ui,self._parameterNode)

    def selectFolder(self):
        self.helper.selectFolder('images',self.ui,self._parameterNode)

            
    # Start segmentation with given thresholds without exporting.
    def startSegmentation(self):
        self._parameterNode.minimumThreshold=self.ui.minimumThreshold.value
        self._parameterNode.maximumThreshold=self.ui.maximumThreshold.value
        if self._parameterNode.maximumThreshold>self._parameterNode.minimumThreshold:
                self.logic.startSegmentation(self._parameterNode.minimumThreshold,self._parameterNode.maximumThreshold,0,self._parameterNode.pathforbone)

        else:
            print('Minimum threshold must be smaller than the maximum threshold')
        

#
# SlicerSegmentationExportLogic
#
class SlicerHelper():
    def setupShortcuts(self,checkForFirst,checkUndo, shortcutKeys, sliceNode, sliceStart, sliceEnd,sliceColor):
        self.logic=SlicerSegmentationExportLogic()
        shortcuts=[]
        if checkForFirst == 0:
            if sliceColor=='red':
             
                # Define the shortcuts using the keys passed in as a parameter
                shortcuts = [
                    (shortcutKeys[0], lambda: self.logic.changeSliceForRed(True, sliceNode, sliceStart, sliceEnd)),
                    (shortcutKeys[1], lambda: self.logic.changeSliceForRed(False, sliceNode, sliceStart, sliceEnd))
                ]
            if sliceColor=='green':
         
                shortcuts = [
                    (shortcutKeys[0], lambda: self.logic.changeSliceForGreen(True, sliceNode, sliceStart, sliceEnd)),
                    (shortcutKeys[1], lambda: self.logic.changeSliceForGreen(False, sliceNode, sliceStart, sliceEnd))
                ]
            if sliceColor=='yellow':
    
                shortcuts = [
                    (shortcutKeys[0], lambda: self.logic.changeSliceForYellow(True, sliceNode, sliceStart, sliceEnd)),
                    (shortcutKeys[1], lambda: self.logic.changeSliceForYellow(False, sliceNode, sliceStart, sliceEnd))
                ]
        if sliceColor=='redo':
            if checkUndo==0:
                shortcuts = [
                    ("Ctrl+z", lambda: self.logic.undo()),
                    ("Ctrl+y", lambda: self.logic.redo())
                    ]

        # Set up the shortcuts
        for (shortcutKey, callback) in shortcuts:
            shortcut = qt.QShortcut(slicer.util.mainWindow())
            shortcut.setKey(qt.QKeySequence(shortcutKey))
            shortcut.connect("activated()", callback)

            
    def selectFolder(self,foldername,ui,parameter):
        folder = QFileDialog.getExistingDirectory(None, 'Select Folder')
       
            
        if folder:
            last_50_chars = folder[-50:]
            if foldername=='images':

                ui.path.setText(last_50_chars)
                parameter.path=folder
                ui.path2.setText(last_50_chars)
            if foldername=='save-scene':
                ui.pathforsavescene.setText(last_50_chars)
                parameter.pathforsavescene=folder
                ui.pathforsavescene2.setText(last_50_chars)
                
            if foldername=='caliber':
                ui.pathforcaliber.setText(last_50_chars)
                parameter.pathforcaliber=folder
                ui.pathforcaliber2.setText(last_50_chars)
                
            if foldername=='bone':
                ui.pathforbone.setText(last_50_chars)
                parameter.pathforbone=folder
                ui.pathforbone2.setText(last_50_chars)
            if foldername=='line':
                ui.pathforline.setText(last_50_chars)
                parameter.pathforline=folder
                ui.pathforline2.setText(last_50_chars)


    def changeSlice(self,direction,sliceNode,minimumOffset,maximumOffset):
        

        dif=maximumOffset-minimumOffset
         
        div=dif/10
        
        
        sliceOffset=sliceNode.GetSliceOffset()
        print(sliceNode.GetSliceOffset())  # Get the current slice offset

        if direction:
            
            
            sliceOffset += div
            if sliceOffset<maximumOffset:
            
                sliceNode.SetSliceOffset(sliceOffset)
                print(sliceNode.GetSliceOffset())
                slicer.app.processEvents()
            else:
                sliceNode.SetSliceOffset(maximumOffset)
        elif not direction:
            
            sliceOffset -= div
            if sliceOffset>minimumOffset:
            
                sliceNode.SetSliceOffset(sliceOffset)
                print(sliceNode.GetSliceOffset())
                slicer.app.processEvents()
            else:
                sliceNode.SetSliceOffset(minimumOffset)
    def calculateGeometry(self,redMiddle,greenMiddle,yellowMiddle):
        firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLVolumeNode')
        origin = firstVolumeNode.GetOrigin()
        spacing = firstVolumeNode.GetSpacing()
        extent = firstVolumeNode.GetImageData().GetExtent()
        redStart=redMiddle-spacing[2]*(extent[5]/2)
        redEnd=redMiddle+spacing[2]*(extent[5]/2)
        greenStart=greenMiddle-spacing[1]*(extent[3]/2)
        greenEnd=greenMiddle+spacing[1]*(extent[3]/2)
        yellowStart=yellowMiddle-spacing[0]*(extent[1]/2)
        yellowEnd=yellowMiddle+spacing[0]*(extent[1]/2)
        redStart+=spacing[2]
        redEnd-=spacing[2]
        yellowStart+=spacing[0]
        yellowEnd-=spacing[0]
        greenStart+=spacing[1]
        greenEnd-=spacing[1]
       


        #print(redStart,redEnd,redMiddle,greenEnd,greenMiddle,yellowStart,yellowEnd,yellowMiddle)
        # if origin[0]<0:
        #     yellowStart=origin[0]
        #     yellowEnd= yellowStart+ spacing[0]*extent[1]
        # else:
        #     yellowEnd=origin[0]
        #     yellowStart= yellowEnd- spacing[0]*extent[1]
            
        # if origin[1]<0:
        #     greenStart=origin[1]
        #     greenEnd= greenStart+ spacing[1]*extent[3]
             
        # else:
        #     greenEnd=origin[1]
             
        #     greenStart= greenEnd- spacing[1]*extent[3]
        # if origin[2]<0:
        #     redStart=origin[2]
        #     redEnd= redStart+ spacing[2]*extent[5]
            
        # else:
        #     redStart=origin[2]
        #     redEnd= redStart+ spacing[2]*extent[5]
        
        return redStart,redEnd,greenStart,greenEnd,yellowStart,yellowEnd

                    
               

class SlicerSegmentationExportLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)
        self.helper=SlicerHelper()

    def getParameterNode(self):
        return SlicerSegmentationExportParameterNode(super().getParameterNode())
    
    # Undo any segment editor operation
    def undo(self):
        segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
        segmentEditorWidget.undo()
     
        slicer.app.processEvents()
        
        
    # Redo any segment editor operation
    def redo(self):
        segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
        segmentEditorWidget.redo()
        slicer.app.processEvents()
     
 
    def deleteLine(self,name):
        deletedline = slicer.util.getNode(name)
        deletedline.RemoveAllControlPoints()
    def generateLine(self, lineLength, x, y, z,path,linename,linenames,num):
        
        if linename=='':
            linename='myline_'+str(num)
        
       
        check=0
        
        for lineName in linenames:
            if lineName==linename:
               check+=1
        
            

       
            

        if path == "":
            print('Please Select a path to extract line!')
        elif check!=0:
            print('There is already line with same name')
        else:
            linenames.append(linename)
            # Create a new line node
            lineNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode', linename)

            lineNode.AddControlPointWorld([x, y, z])
            lineNode.AddControlPointWorld([x, y+ lineLength, z ])



            # Set line display properties
            lineDisplayNode = lineNode.GetDisplayNode()
            lineDisplayNode.SetColor([1, 0, 0])  # Red color
            lineDisplayNode.SetLineWidth(2)  # Line thickness

            # Adjust 3D view
            layoutManager = slicer.app.layoutManager()
            threeDWidget = layoutManager.threeDWidget(0)
            threeDView = threeDWidget.threeDView()
            threeDView.rotateToViewAxis(3)  # Look from anterior direction
            threeDView.resetFocalPoint()  # Reset the 3D view cube size and center it
            threeDView.resetCamera()  # Reset camera zoom

            colors = vtkNamedColors()


            if x==0 and y==0 and z==0:
                    # Create a line
                lineSource = vtkLineSource()
                lineSource.SetPoint1(x, y, z)
                lineSource.SetPoint2(x, y, z + lineLength)
            else:
                lineSource = vtkLineSource()
                lineSource.SetPoint1(x, y, z)
                lineSource.SetPoint2(x, y, z + lineLength)

            

            # Setup actor and mapper
            lineMapper = vtkPolyDataMapper()
            lineMapper.SetInputConnection(lineSource.GetOutputPort())

            lineActor = vtkActor()
            lineActor.SetMapper(lineMapper)
            lineActor.GetProperty().SetColor(colors.GetColor3d('Red'))

            # Create tube filter
            tubeFilter = vtkTubeFilter()
            tubeFilter.SetInputConnection(lineSource.GetOutputPort())
            tubeFilter.SetRadius(0.25)
            tubeFilter.SetNumberOfSides(50)
            tubeFilter.Update()

            # Setup actor and mapper
            tubeMapper = vtkPolyDataMapper()
            tubeMapper.SetInputConnection(tubeFilter.GetOutputPort())

            tubeActor = vtkActor()
            tubeActor.SetMapper(tubeMapper)
            # Make the tube have some transparency.
            tubeActor.GetProperty().SetOpacity(0.5)

            # Setup render window, renderer, and interactor



            modelsLogic = slicer.modules.models.logic()
            model = modelsLogic.AddModel(tubeFilter.GetOutputPort())
            model.GetDisplayNode().SetVisibility2D(True)
            model.GetDisplayNode().SetSliceIntersectionThickness(3)
            model.GetDisplayNode().SetColor(1,1,0)



            linepath= os.path.join(path,linename + ".obj")
            plyFilePath = linepath



            modelDisplayNode = model.GetDisplayNode()
            triangles = vtk.vtkTriangleFilter()
            triangles.SetInputConnection(modelDisplayNode.GetOutputMeshConnection())




            plyWriter = vtk.vtkOBJWriter()
            plyWriter.SetInputConnection(triangles.GetOutputPort())

             

            plyWriter.SetFileName(plyFilePath)
            plyWriter.Write()


    def Erase(self):
        segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
        segmentEditorWidget.setActiveEffectByName("Erase")
        eraseEffect = segmentEditorWidget.activeEffect()
        eraseEffect.setParameter("BrushRelativeDiameter", 25.0)
        eraseEffect.setParameter("EraseAllSegments", 1)
        eraseEffect.setParameter("BrushSphere", 1)
    
   

               
    def changeSliceForRed(self,direction,sliceNode,minimumOffset,maximumOffset):
        # Declare sliceOffset as global to modify it
        # Get the layout manager and slice widget
        
        
        self.helper.changeSlice(direction,sliceNode,minimumOffset,maximumOffset)
    
    def changeSliceForGreen(self,direction,sliceNode,minimumOffset,maximumOffset):
        # Declare sliceOffset as global to modify it
        # Get the layout manager and slice widget
        self.helper.changeSlice(direction,sliceNode,minimumOffset,maximumOffset)
    def changeSliceForYellow(self,direction,sliceNode,minimumOffset,maximumOffset):
        # Declare sliceOffset as global to modify it
        # Get the layout manager and slice widget
        
        self.helper.changeSlice(direction,sliceNode,minimumOffset,maximumOffset)
    def exportPaint(self,pathforpaint):
       # Get the segmentation node
        paintNode = slicer.mrmlScene.GetFirstNodeByName("paint-node")

        # Get the segmentation object from the node
        segmentation = paintNode.GetSegmentation()

        # Initialize an array to hold all segment IDs
        segmentIDArray = vtk.vtkStringArray()

        # Loop through all segments in the segmentation and add their IDs to the array
        for i in range(segmentation.GetNumberOfSegments()):
            segmentId = segmentation.GetNthSegmentID(i)
            segmentIDArray.InsertNextValue(segmentId)

        # Define the output folder
        outputFolder = pathforpaint
        outputFolder = os.path.join(pathforpaint, "Model_Obj_Export_caliber")

    # Create the directory if it doesn't exist
        if not os.path.exists(outputFolder):
            os.makedirs(outputFolder)

        # Export all segments to OBJ files
        slicer.vtkSlicerSegmentationsModuleLogic.ExportSegmentsClosedSurfaceRepresentationToFiles(
            outputFolder, paintNode, segmentIDArray, "OBJ", True, 1.0, False
        )
    def createCaliberAtCorners(self,segmentationNode,baselineVolume):

        # Create segments in segmentation node
        segmentId1 = segmentationNode.GetSegmentation().AddEmptySegment("Caliber-Segment")



        # Access the current volume and segmentation nodes
        volumeNode = baselineVolume

        segmentId = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName('Caliber-Segment')

        # Get the segmentation as a numpy array
        segmentArray = slicer.util.arrayFromSegmentBinaryLabelmap(segmentationNode, segmentId, volumeNode)

        # Clear the segmentation (optional if you want to start with an empty segment)
        segmentArray[:] = 0  
        # Define the radius of the quarter spheres
        radius = 50  # Adjust this as necessary for your case
 
        zmax=0
        ymax=0
        xmax=0
        firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLVolumeNode')
        spacing = firstVolumeNode.GetSpacing()
        spacingX, spacingY, spacingZ = spacing

        # Calculate the radius in voxel coordinates for each axis
        radiusX = int(radius / spacingX)
        radiusY = int(radius / spacingY)
        radiusZ = int(radius / spacingZ)

        # Loop through each slice (z dimension)
        for z in range(radiusZ):  # Iterate through each slice (axial view)
            for x in range(radiusX):
                for y in range(radiusY):
                    # Calculate the distance from the corner in mm
                    distance = np.sqrt((x * spacingX) ** 2 + (y * spacingY) ** 2 + (z * spacingZ) ** 2)

                    # Check if within sphere radius, and fill in quarter spheres
                    if distance < radius:
                        # Top-left corner
                        segmentArray[int(z), x, y] = 1
                        # Top-right corner
                        segmentArray[int(z), -x-1, y] = 1
                        # Bottom-left corner
                        segmentArray[int(z), x, -y-1] = 1
                        # Bottom-right corner
                        segmentArray[int(z), -x-1, -y-1] = 1

      

                    

        # Update the segmentation with the modified array
        slicer.util.updateSegmentBinaryLabelmapFromArray(segmentArray, segmentationNode, segmentId, volumeNode)


        # Define the radius of the quarter spheres
        radius = 100 # Adjust this as necessary for your case
        spacingX, spacingY, spacingZ = spacing

        # Calculate the radius in voxel coordinates for each axis
        radiusX = int(radius / spacingX)
        radiusY = int(radius / spacingY)
        radiusZ = int(radius / spacingZ)

        # Start from the last couple of slices (based on the radius)
        numSlices = segmentArray.shape[0]  # Number of slices in the z-axis

        # Loop through the last `radiusZ` slices
        for z in range(numSlices - radiusZ, numSlices):  # Iterate over the last `radiusZ` slices
            z_offset = numSlices - z  # Calculate relative position from the last slice

            for x in range(radiusX):
                for y in range(radiusY):
                    # Calculate the distance from the corner in mm, using the z_offset for relative z
                    distance = np.sqrt((x * spacingX) ** 2 + (y * spacingY) ** 2 + (z_offset * spacingZ) ** 2)

                    # Check if within sphere radius, and fill in quarter spheres
                    if distance <= radius:
                        # Ensure the z index is within bounds
                        if z < numSlices:
                            # Top-left corner
                            segmentArray[z, x, y] = 1
                            # Top-right corner
                            segmentArray[z, -x-1, y] = 1
                            # Bottom-left corner
                            segmentArray[z, x, -y-1] = 1
                            # Bottom-right corner
                            segmentArray[z, -x-1, -y-1] = 1

        # Update the segmentation with the modified array
        slicer.util.updateSegmentBinaryLabelmapFromArray(segmentArray, segmentationNode, segmentId, volumeNode)
        segmentationNode.CreateClosedSurfaceRepresentation()

    def selectPaint(self,baselineVolume,diameter,sliceName,sliceNode,checkForFirst,segmentationNode,redMiddle,greenMiddle,yellowMiddle)->None:
        # Create segmentation node
        
        segmentationNode.CreateDefaultDisplayNodes()

        # Create segments in segmentation node
        segmentId1 = segmentationNode.GetSegmentation().AddEmptySegment("Paint-Segment")

        # Set segment IDs for painting
        region1SegmentId = segmentId1

        # Create segment editor to get access to effects
        slicer.app.processEvents()
        segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        # To show segment editor widget (useful for debugging): segmentEditorWidget.show()
        segmentEditorWidget.setMRMLScene(slicer.mrmlScene)


        # Create segment editor node to use segment editor operations
        segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
        
        slicer.mrmlScene.AddNode(segmentEditorNode)
 

        # Necessary for using segment editor widget in code
        segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
        segmentEditorWidget.setSegmentationNode(segmentationNode)
        segmentEditorWidget.setSourceVolumeNode(baselineVolume)
        

        # Select the segment editor
        slicer.util.selectModule('SegmentEditor')
        segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
        segmentEditorNode = segmentEditorWidget.mrmlSegmentEditorNode()
        segmentEditorNode.SetAndObserveSegmentationNode(segmentationNode)
        segmentEditorNode.SetAndObserveSourceVolumeNode(baselineVolume)
        # Return back to extension
        slicer.util.selectModule('SlicerSegmentationExport')
        

        

        # Select paint brush from segment editor effects
        segmentEditorWidget.setActiveEffectByName("Paint")
        paintEffect = segmentEditorWidget.activeEffect()
        paintEffect.setParameter("BrushRelativeDiameter", diameter)
        paintEffect.setParameter("BrushSphere", 1)
        
        
        

                                                

        segmentEditorNode.SetSelectedSegmentID(region1SegmentId)
        slicer.app.processEvents()
        

    
        redStart,redEnd,greenStart,greenEnd,yellowStart,yellowEnd= self.helper.calculateGeometry(redMiddle,greenMiddle,yellowMiddle)



 
        if sliceName=='red':
  

            shortcutKeys=["Ctrl+q","Ctrl+e"]
            self.helper.setupShortcuts(checkForFirst,-1, shortcutKeys, sliceNode, redStart, redEnd,'red')
           
                
                
 
            if diameter==10.0:

                sliceNode.SetSliceOffset(redStart)
            elif diameter==20.0:

                sliceNode.SetSliceOffset(redEnd)
        if sliceName=='green':
            
      
        
            shortcutKeys=["Ctrl+a","Ctrl+d"]
            self.helper.setupShortcuts(checkForFirst,-1, shortcutKeys, sliceNode, greenStart, greenEnd,'green')
           
            
            
            if diameter==10:
                sliceNode.SetSliceOffset(greenStart+30)
            elif diameter==20:
                sliceNode.SetSliceOffset(greenEnd-30)
                
        if sliceName=='yellow':
        
            shortcutKeys=["Ctrl+x","Ctrl+v"]
            self.helper.setupShortcuts(checkForFirst,-1, shortcutKeys, sliceNode, yellowStart, yellowEnd,'yellow')
           
            
          
            
            
            if diameter==10:
                sliceNode.SetSliceOffset(yellowStart+30)
            elif diameter==20:
                sliceNode.SetSliceOffset(yellowEnd-30)
        slicer.app.processEvents()
        segmentEditorNode.SetSelectedSegmentID(region1SegmentId)
        segmentationNode.CreateClosedSurfaceRepresentation()
     
 
            
    

    # ZIP folders that contain dicom images under the DICOM.zip file
    def zipImages(self,path):
        if path != "":
            print(path)
            with_image_folder = os.path.join(path, "With-Paint").replace("\\", "/")
            without_image_folder = os.path.join(path, "Without-Paint").replace("\\", "/")
            dicom_folder = os.path.join(path, "DICOM").replace("\\", "/")
            archive_path = os.path.join(path, "DICOM.zip").replace("\\", "/")
            
            with_image_exists = os.path.isdir(with_image_folder)
            without_image_exists = os.path.isdir(without_image_folder)
 
            if with_image_exists or without_image_exists:
                 
                os.makedirs(dicom_folder, exist_ok=True)
                
                if os.path.exists(with_image_folder):
                    shutil.copytree(with_image_folder, os.path.join(dicom_folder, 'With-Paint'), dirs_exist_ok=True)
                if os.path.exists(without_image_folder):
                    shutil.copytree(without_image_folder, os.path.join(dicom_folder, 'Without-Paint'), dirs_exist_ok=True)

                # Archive the contents of the DICOM folder without including the DICOM folder itself
                archived = shutil.make_archive(dicom_folder, 'zip', root_dir=dicom_folder, base_dir='.')

                if os.path.exists(archive_path):
                   print(archived) 
                else: 
                   print("ZIP file not created")
                shutil.rmtree(with_image_folder)
                shutil.rmtree(without_image_folder)
                shutil.rmtree(dicom_folder)
        else:
            print("Path must be given to zip images!")
                
    
    def exportImages(self,path,imageNumber,green_slice,red_slice,yellow_slice,SSPaintInclude,redMiddle,greenMiddle,yellowMiddle):
        # Create segmentation node for finding slice geometry
        print(path)
        try:
            segmentationNodes = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')
            segmentationNode=segmentationNodes[0]
                     
        except:
            segmentationNodes = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode","node-for-index")
            
            segmentationNodes = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')
            segmentationNode=segmentationNodes[0]
  
        imageNumber=int(imageNumber)


        # Create segments in segmentation node
        segmentId1 = segmentationNode.GetSegmentation().AddEmptySegment("Paint-Segment")

        # Set segment IDs for painting
        region1SegmentId = segmentId1

        # Create segment editor to get access to effects
        slicer.app.processEvents()
        segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        # To show segment editor widget (useful for debugging): segmentEditorWidget.show()
        segmentEditorWidget.setMRMLScene(slicer.mrmlScene)

        segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
        
        slicer.mrmlScene.AddNode(segmentEditorNode)
 
        segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
        segmentEditorWidget.setSegmentationNode(segmentationNode)

        segmentEditorNode.SetSelectedSegmentID(region1SegmentId)
        slicer.app.processEvents()



        redStart,redEnd,greenStart,greenEnd,yellowStart,yellowEnd= self.helper.calculateGeometry(redMiddle,greenMiddle,yellowMiddle)









        if path=="":
            logging.error("No folder fath is given for screen capture!")
        else:
        
            try:
                paintLayer = getNode('paint-node')
                paintLayerExists = True
            except slicer.util.MRMLNodeNotFoundException:
                paintLayerExists = False
            files = os.listdir(path)
            # Check if there are other images
            images = [file for file in files if file.endswith('.png')]
            
            if images:
                logging.error("Please Select Empty Folder!")
            else:
                
                withpaint=os.path.join(path, "With-Paint")
                withoutpaint=os.path.join(path, "Without-Paint")
                if not os.path.exists(withpaint):
                    os.makedirs(withpaint)
                if not os.path.exists(withoutpaint):
                    os.makedirs(withoutpaint)
                if paintLayerExists:
                
                    if SSPaintInclude:
                        new_dir = []
                        paintLayer = getNode('paint-node')  # Adjust this based on your actual layer name
                        paintLayer.SetDisplayVisibility(1)  # 0 to hide, 1 to show

                  
                        if red_slice:
                            new_dir.append('Axial')
                            withpaintaxial = os.path.join(withpaint, new_dir[-1])
                            if not os.path.exists(withpaintaxial):
                                os.makedirs(withpaintaxial)
                            
                            
                            
                            
                            
                            # Get slice image captures
                            ScreenCapture.ScreenCaptureLogic().captureSliceSweep(getNode("vtkMRMLSliceNodeRed"), redStart, redEnd,imageNumber , withpaintaxial, "imageRed_%05d.png" )
                    
                        if green_slice:


                            new_dir.append('Coronal')
                            withpaintcoronal = os.path.join(withpaint, new_dir[-1])
                            if not os.path.exists(withpaintcoronal):
                                os.makedirs(withpaintcoronal)
        
                          
                            # Get slice image captures
                            ScreenCapture.ScreenCaptureLogic().captureSliceSweep(getNode("vtkMRMLSliceNodeGreen"), greenStart, greenEnd,imageNumber , withpaintcoronal, "imageGreen_%05d.png" )
                    
                        if yellow_slice:
                            new_dir.append('Sagittal')
                            withpaintsagittal = os.path.join(withpaint, new_dir[-1])
                            if not os.path.exists(withpaintsagittal):
                                os.makedirs(withpaintsagittal)
                            
                            
       
                            # Get slice image captures
                            ScreenCapture.ScreenCaptureLogic().captureSliceSweep(getNode("vtkMRMLSliceNodeYellow"), yellowStart, yellowEnd,imageNumber , withpaintsagittal, "imageYellow_%05d.png" )
   
                    
                    else:
                        new_dir = []

                        paintLayer = getNode('paint-node')  # Adjust this based on your actual layer name
                        paintLayer.SetDisplayVisibility(0)  # 0 to hide, 1 to show

                        if red_slice:

                            new_dir.append('Axial')
                            axial_withoutpaint= os.path.join(withoutpaint, new_dir[-1])
                            if not os.path.exists(axial_withoutpaint):
                                os.makedirs(axial_withoutpaint) 
                            
                                                  # Get slice image captures
                            ScreenCapture.ScreenCaptureLogic().captureSliceSweep(getNode("vtkMRMLSliceNodeRed"), redStart, redEnd,imageNumber , axial_withoutpaint, "imageRed_%05d.png" )
                        if green_slice:
                            new_dir.append('Coronal')
                            coronal_withoutpaint= os.path.join(withoutpaint, new_dir[-1])
                            if not os.path.exists(coronal_withoutpaint):
                                os.makedirs(coronal_withoutpaint) 
                            
                       
                            # Get slice image captures
                            ScreenCapture.ScreenCaptureLogic().captureSliceSweep(getNode("vtkMRMLSliceNodeGreen"), greenStart, greenEnd,imageNumber , coronal_withoutpaint, "imageGreen_%05d.png" )
                        if yellow_slice:
                            new_dir.append('Sagittal')
                            sagittal_withoutpaint= os.path.join(withoutpaint, new_dir[-1])
                            if not os.path.exists(sagittal_withoutpaint):
                                os.makedirs(sagittal_withoutpaint) 
                            
                       
                            # Get slice image captures
                            ScreenCapture.ScreenCaptureLogic().captureSliceSweep(getNode("vtkMRMLSliceNodeYellow"), yellowStart, yellowEnd,imageNumber , sagittal_withoutpaint, "imageYellow_%05d.png" )


                else:
                    new_dir = []
                    if red_slice:
                        new_dir.append('Axial')
                        withoutpaintaxial = os.path.join(withoutpaint, new_dir[-1])
                        if not os.path.exists(withoutpaintaxial):
                            os.makedirs(withoutpaintaxial)
                        
                        
                        
                        
                        
                                                    # Get slice image captures
                        ScreenCapture.ScreenCaptureLogic().captureSliceSweep(getNode("vtkMRMLSliceNodeRed"), redStart, redEnd,imageNumber , withoutpaintaxial, "imageRed_%05d.png" )
                    if green_slice:
                        new_dir.append('Coronal')
                        withoutpaintcoronal = os.path.join(withoutpaint, new_dir[-1])
                        if not os.path.exists(withoutpaintcoronal):
                            os.makedirs(withoutpaintcoronal)
                        
                        
                        
                        
                        
                                                    # Get slice image captures
                        ScreenCapture.ScreenCaptureLogic().captureSliceSweep(getNode("vtkMRMLSliceNodeGreen"), greenStart, greenEnd,imageNumber , withoutpaintcoronal, "imageGreen_%05d.png" )
                    if yellow_slice:
                        new_dir.append('Sagittal')
                        withoutpaintsagittal = os.path.join(withoutpaint, new_dir[-1])
                        if not os.path.exists(withoutpaintsagittal):
                            os.makedirs(withoutpaintsagittal)
                        
                        
                        
                        
                        
                                                    # Get slice image captures
                        ScreenCapture.ScreenCaptureLogic().captureSliceSweep(getNode("vtkMRMLSliceNodeYellow"), yellowStart, yellowEnd,imageNumber , withoutpaintsagittal, "imageYellow_%05d.png" )





        
    def startSegmentation(self,minimumThreshold,maximumThreshold,checkForExport,pathforbone):


        masterVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
        smoothingKernelSizeMm = 0.6  






        

      




        segmentationNode = slicer.mrmlScene.GetFirstNodeByName("MySegmentationNode")
        if segmentationNode is not None:
            slicer.mrmlScene.RemoveNode(segmentationNode)

            


        segmentationNode = slicer.vtkMRMLSegmentationNode()
        segmentationNode.SetName("MySegmentationNode")
        slicer.mrmlScene.AddNode(segmentationNode)

          # Create segmentation
        slicer.app.processEvents()
        
        segmentationNode.CreateDefaultDisplayNodes() # only needed for display
        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)

        # Create segment editor to get access to effects
        slicer.app.processEvents()
        segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        segmentEditorWidget.setMRMLScene(slicer.mrmlScene)


        segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
        slicer.mrmlScene.AddNode(segmentEditorNode)
 
        segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
        segmentEditorWidget.setSegmentationNode(segmentationNode)
        segmentEditorWidget.setSourceVolumeNode(masterVolumeNode)
        
        # Create bone segment by thresholding
        slicer.app.processEvents()
        boneSegmentID = segmentationNode.GetSegmentation().AddEmptySegment("MySegment")
        segmentEditorNode.SetSelectedSegmentID(boneSegmentID)
        segmentEditorWidget.setActiveEffectByName("Threshold")
        effect = segmentEditorWidget.activeEffect()
        effect.setParameter("MinimumThreshold",minimumThreshold)
        effect.setParameter("MaximumThreshold",maximumThreshold)
        effect.self().onApply()

        # Smooth bone segment (just to reduce solidification computation time)
        slicer.app.processEvents()
        segmentEditorWidget.setActiveEffectByName("Smoothing")
        effect = segmentEditorWidget.activeEffect()
        effect.setParameter("SmoothingMethod", "GAUSSIAN")
        effect.setParameter("GaussianStandardDeviationMm", str(smoothingKernelSizeMm))
        effect.self().onApply()


        # Make segmentation results nicely visible in 3D
        segmentationDisplayNode = segmentationNode.GetDisplayNode()
        segmentationDisplayNode.SetSegmentOpacity3D(boneSegmentID, 0.4)
        segmentationNode.CreateClosedSurfaceRepresentation()


        # Clean up
        slicer.mrmlScene.RemoveNode(segmentEditorNode)

        # Make segmentation results nicely visible in 3D
        segmentationDisplayNode = segmentationNode.GetDisplayNode()
        
     
        segmentIDs = vtk.vtkStringArray()
        segmentIDs.InsertNextValue(boneSegmentID)
        if(checkForExport==1):
 
            outputFolder = pathforbone
            outputFolder = os.path.join(pathforbone, "Model_Obj_Export_Segmentation")

            # Create the directory if it doesn't exist
            if not os.path.exists(outputFolder):
                os.makedirs(outputFolder)

            # Export path to given path
            slicer.vtkSlicerSegmentationsModuleLogic.ExportSegmentsClosedSurfaceRepresentationToFiles(outputFolder, segmentationNode, segmentIDs, "OBJ", True, 1.0, False)
            
         
        

        
       
        

        
        

     



   