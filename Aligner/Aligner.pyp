"""
ALIGNER Tool V-0.05

Written for Cinema 4D R16
By Andrez Aguayo @ DK Studios Chicago

Modified Date: 11/04/2015

This is my first ever Plugin for anything ever! So I am assuming there will be bugs
and some over all code that could be avoided.

This Tool is inspired by the 3dsMax defult Align tool.

Usage: Select one or more object you want to align, then run the tool,
now connect a target object and align! Gives the options of seperating out Translation,
Rotation, and Scale.


V 0.02 Updates 
- You can now select object in the viewport for quickly aligning something 
- A preview guide line is now drawn in the viewport when you hover over a potential 
object to align to 
- Esc button now exits the tool and enables select mode 
- Added a Cancel button if you want to exit the tool and rest original position 
- Ok button exits the tool and enables select mode 

v 0.03 Updates
- Added Axis support! Now align the objects axis point if is a point type object(Spline, Poly)
-Changed the name Pivot Point to Axis point on GUI, Because it is more consistant to the Cinema Terminology

v 0.04 Updates 
- Separated X, Y, Z on Min, Max and Center option  

v.05 Updates 
- Undo Align support 
- Tool name change to just Aligner
- Bug fix- clears all splines when tool is changed 
"""
import c4d
import os
from c4d import gui, plugins, bitmaps


#be sure to use a unique ID obtained from www.plugincafe.com
PLUGIN_ID = 1036262

#Global UI Elements
IDS_PRIMITIVETOOL = 50000
TXT_POS_WORLD = 909752001
TXT_ROT_LOCAL = 909752002
TXT_SCL_LOCAL = 909752003
CHKBOX_POS_X = 909752004
CHKBOX_POS_Y = 909752005
CHKBOX_POS_Z = 909752006
CHKBOX_ROT_X = 909752007
CHKBOX_ROT_Y = 909752008
CHKBOX_ROT_Z = 909752009
CHKBOX_SCL_X = 909752010
CHKBOX_SCL_Y = 909752011
CHKBOX_SCL_Z = 909752012
BTN_PST = 909752013
BTN_OK = 909752014
BTN_CNL = 909752015
GROUP_POS = 909752016
GROUP_ROT = 909752017
GROUP_SCL = 909752018
GROUP_OK_CNL = 909752019
RDO_GRP = 909752020
RDO_GRP2 = 909752021
MY_LINKBOX =909752022
GROUP_POS2 = 909752023
BTN_CNL2 =909752024

### First a little bit of align functions that will do the dirty work of the plug in Max Align
def overide_specific_matrix_values(AMg, BMg, AScl, BScl, objectA, objectB,
                                   curPivType=3, tarPivType=3,
                                   posX=True, posY=True, posZ=True,
                                   rotX=False, rotY=False, rotZ=False,
                                   sclX=False, sclY=False, sclZ=False):
    ## create a transform matrix depending on you want to change
    newAMg = c4d.Matrix()
    newV1 = c4d.Vector()
    newV2 = c4d.Vector()
    newV3 = c4d.Vector()
    newScl = c4d.Vector()
    ## assining objectA matrix values to the new matrix
    newV1 = AMg.v1
    newV2 = AMg.v2
    newV3 = AMg.v3
    newAMg.off = AMg.off
    newAMg.v1 = newV1
    newAMg.v2 = newV2
    newAMg.v3 = newV3
    newScl = AScl

    ## Start Building the new
    if posX:
        #Build new Vector switching X object then set it
        v = c4d.Vector(BMg.off.x, newAMg.off.y, newAMg.off.z)
        newAMg.off = v
    if posY:
        #Build new Vector switching Y object then set it
        v = c4d.Vector(newAMg.off.x, BMg.off.y, newAMg.off.z)
        newAMg.off = v
    if posZ:
        #Build new Vector switching Z object then set it
        v = c4d.Vector(newAMg.off.x, newAMg.off.y, BMg.off.z)
        newAMg.off = v
    if rotX:
        newAMg.v1 = BMg.v1
    if rotY:
        newAMg.v2 = BMg.v2
    if rotZ:
        newAMg.v3 = BMg.v3
    if sclX:
        v = c4d.Vector(BScl.x, newScl.y, newScl.z)
        newScl= v
    if sclY:
        v = c4d.Vector(newScl.x, BScl.y, newScl.z)
        newScl= v
    if sclZ:
        v = c4d.Vector(newScl.x, newScl.y, BScl.z)
        newScl= v

    objectA.SetMg(newAMg)
    objectA.SetAbsScale(newScl)
    # If the object has a positon offset (Center, Min, or Max) apply that offset
    if posX or posY or posZ:
        newAMg = add_current_offsetMatrix(newAMg, objectA, curPivType,posX,posY,posZ)
        newAMg = add_target_offsetMatrix(newAMg, objectA, objectB, tarPivType,posX,posY,posZ)

    c4d.EventAdd()
    return newAMg, newScl


def move_current_center_to(myObject,toMin,toMax,toPivot,X,Y,Z):
    #print "X, Y, Z"
    #print X, Y, Z
    if toMin or toMax:
        offset = myObject.GetRad()
    else:#toPivot
        offset = myObject.GetMp()

    theMg = myObject.GetMg()
    
    newM = c4d.Matrix()


    if not X:
        offset.x = 0.0
    if not Y:
        offset.y = 0.0
    if not Z:
        offset.z = 0.0


    if toPivot or toMax:
        newM.off = -offset        
    else: #To Max
        newM.off = offset
    
    #print "this is newM"
    #print newM.off

    bob1 = theMg*newM

    ## bob is postion for 0 to move to
    myObject.SetMg(bob1)

    mat = myObject.GetMg()
    return mat

def add_current_offsetMatrix(aMatrix, c4dObject,pivotType,X,Y,Z):
    #1 = Minimum #2 = Center #3 = Pivot Point #4 = Maximum
    if pivotType == 1:
        #print("Still working on getting Minimum working")
        #aMatrix = move_center_to_min(c4dObject)

        aMatrix = move_current_center_to(c4dObject,True,False,False,X,Y,Z)
        return aMatrix

    elif pivotType == 2:
        #aMatrix = move_center_to_pivot(c4dObject)
        aMatrix = move_current_center_to(c4dObject,False,False,True,X,Y,Z)
        return aMatrix

    elif pivotType == 3:
        # It already works based off pivot, do nothing
        return aMatrix

    elif pivotType == 4:
        #aMatrix = move_center_to_max(c4dObject)
        aMatrix = move_current_center_to(c4dObject,False,True,False,X,Y,Z)
        return aMatrix

def add_target_offsetMatrix(aMatrix, c4dObjectA, c4dObject,pivotType,X,Y,Z):
    #1 = Minimum #2 = Center #3 = Pivot Point #4 = Maximum
    if pivotType == 1:
        # Get the targets objects center offset
        centerV = c4dObject.GetRad()
        # Create a new c4d matrix to use to multiply the object
        newMat = c4d.Matrix()
        # put in the negative value of the cetner point into the new matrix
        newMat.off = centerV

        # Caculate the matrix of the offset
        targetMg = c4dObject.GetMg()
        targetMatrixOffset = targetMg*newMat
        #now subtract the target offset from the object position to get a world space offest
        offVec = targetMg.off - targetMatrixOffset.off
        #print "Print this is off Vec"
        #print offVec
        if not X:
            offVec.x = 0.0
        if not Y:
            offVec.y = 0.0
        if not Z:
            offVec.z = 0.0

        aMatrix.off += offVec
        #aMatrix.off = newMat.off
        c4dObjectA.SetMg(aMatrix)
        return aMatrix

    elif pivotType == 2:
        # Get the targets objects center offset
        centerV = c4dObject.GetMp()
        # Create a new c4d matrix to use to multiply the object
        newMat = c4d.Matrix()
        # put in the negative value of the cetner point into the new matrix
        newMat.off = -centerV
        # Caculate the matrix of the offset
        targetMg = c4dObject.GetMg()
        targetMatrixOffset = targetMg*newMat
        #now subtract the target offset from the object position to get a world space offest
        offVec = targetMg.off - targetMatrixOffset.off
        #print "Print this is off Vec"
        #print offVec
        if not X:
            offVec.x = 0.0
        if not Y:
            offVec.y = 0.0
        if not Z:
            offVec.z = 0.0

        aMatrix.off += offVec
        #aMatrix.off = newMat.off
        c4dObjectA.SetMg(aMatrix)
        return aMatrix

    elif pivotType == 3:
        # It already works based off pivot, do nothing
        return aMatrix

    elif pivotType == 4:
        # Get the targets objects center offset
        centerV = c4dObject.GetRad()
        # Create a new c4d matrix to use to multiply the object
        newMat = c4d.Matrix()
        # put in the negative value of the cetner point into the new matrix
        newMat.off = -centerV

        # Caculate the matrix of the offset
        targetMg = c4dObject.GetMg()
        targetMatrixOffset = targetMg*newMat
        #now subtract the target offset from the object position to get a world space offest
        offVec = targetMg.off - targetMatrixOffset.off
        #print "Print this is off Vec"
        #print offVec
        if not X:
            offVec.x = 0.0
        if not Y:
            offVec.y = 0.0
        if not Z:
            offVec.z = 0.0

        aMatrix.off += offVec
        #aMatrix.off = newMat.off
        c4dObjectA.SetMg(aMatrix)
        return aMatrix

class SettingsDialog(gui.SubDialog):
    def __init__(self, arg, arg2, arg3,arg4,arg5,arg6,arg7):
        self.CurrentObjects = arg
        self.CurrentObjectsMg = arg2
        self.CurrentObjectsScale = arg3
        self.targetObject = arg4
        self.axisMode = arg5
        self.points = arg6
        self.pcount = arg7

    def CreateLayout(self):
        #self.ok = True
        self.SetTitle('Aligner')

        self.linkBox = self.AddCustomGui(MY_LINKBOX, c4d.CUSTOMGUI_LINKBOX,"",c4d.BFH_SCALEFIT,0,0)
        #self.linkBox.SetLink(None)q
        self.linkBox.SetLink(self.targetObject["targetObject"])

        self.GroupBegin(1351354, c4d.BFH_LEFT, 2, 1,title="Align Position(World): ")
        # Add static text labelS
        self.AddStaticText(TXT_POS_WORLD, c4d.BFH_LEFT | c4d.BFV_TOP)
        self.SetString(TXT_POS_WORLD, "Position(World):    ")
        # Create group to add gui elements to
        self.GroupBegin(GROUP_POS, c4d.BFH_CENTER, 3, 1,title="Align Position(World):", initw = 80)#groupflags = c4d.BFV_BORDERGROUP_CHECKBOX)
        #self.GroupBegin(GROUP_OPTIONS2, c4d.BFV_TOP, 1, 1)
        # Add Check box Elements, and set to the current clip board
        self.AddCheckbox(CHKBOX_POS_X, c4d.BFH_LEFT, initw=125, inith=8, name="X")
        self.AddCheckbox(CHKBOX_POS_Y, c4d.BFH_LEFT, initw=125, inith=8, name="Y")
        self.AddCheckbox(CHKBOX_POS_Z, c4d.BFH_LEFT, initw=125, inith=8, name="Z")
        self.SetBool(CHKBOX_POS_X,True)
        self.SetBool(CHKBOX_POS_Y,True)
        self.SetBool(CHKBOX_POS_Z,True)
        self.AddStaticText(652213, c4d.BFH_LEFT, inith=0)
        self.GroupEnd()
        self.GroupEnd()

        self.GroupBegin(64653133, c4d.BFH_LEFT, 4, 1)
        self.AddStaticText(445555, c4d.BFH_LEFT | c4d.BFV_TOP, initw=140)
        self.SetString(445555, "Current Object:")

        # Add Radio Group elements, and set to the current clip board
        self.AddRadioGroup(RDO_GRP, c4d.BFV_TOP, 1)
        self.AddChild(RDO_GRP, 1, 'Minumum           ')
        self.AddChild(RDO_GRP, 2, 'Center')
        self.AddChild(RDO_GRP, 3, 'Axis Point')
        self.AddChild(RDO_GRP, 4, 'Maximum')
        self.SetInt32(RDO_GRP,3)

        self.AddStaticText(446555, c4d.BFH_LEFT | c4d.BFV_TOP, initw=135)
        self.SetString(446555, "Target Object:")

        # Add Radio Group elements, and set to the current clip board
        self.AddRadioGroup(RDO_GRP2, c4d.BFV_TOP, 1)
        self.AddChild(RDO_GRP2, 1, 'Minumum')
        self.AddChild(RDO_GRP2, 2, 'Center')
        self.AddChild(RDO_GRP2, 3, 'Axis Point')
        self.AddChild(RDO_GRP2, 4, 'Maximum')
        self.SetInt32(RDO_GRP2,3)
        self.GroupEnd()

        self.AddSeparatorH(25,c4d.BFH_SCALEFIT)

        # Add static text label
        self.GroupBegin(32522566,c4d.BFH_LEFT, 2, 1, title="Group22")
        self.AddStaticText(TXT_ROT_LOCAL, c4d.BFH_LEFT)
        self.SetString(TXT_ROT_LOCAL, "Orientation(Local):")
        # Create Group to add gui elements to
        self.GroupBegin(GROUP_ROT, c4d.BFH_LEFT, 3, 1,title="Align Orientation Grp", initw = 80)#groupflags = c4d.BFV_BORDERGROUP_CHECKBOX)
        #self.GroupBegin(GROUP_OPTIONS2, c4d.BFV_TOP, 1, 1)
        # Add Rad Group elements, and set to the current clip board
        self.AddCheckbox(CHKBOX_ROT_X, c4d.BFH_LEFT, initw=125, inith=8, name="X")
        self.AddCheckbox(CHKBOX_ROT_Y, c4d.BFH_LEFT, initw=125, inith=8, name="Y")
        self.AddCheckbox(CHKBOX_ROT_Z, c4d.BFH_LEFT, initw=125, inith=8, name="Z")
        self.GroupEnd()
        self.GroupEnd()

        self.AddSeparatorH(25,c4d.BFH_SCALEFIT)

        # Add static text label
        self.GroupBegin(22522566,c4d.BFH_LEFT, 2, 1, title="Group")
        self.AddStaticText(TXT_SCL_LOCAL, c4d.BFH_LEFT)
        self.SetString(TXT_SCL_LOCAL, "Scale Axis(Local):    ")
        # Create Group to add gui elements to
        self.GroupBegin(GROUP_SCL, c4d.BFH_LEFT, 3, 1,title="Align scale grp:", initw = 80)#groupflags = c4d.BFV_BORDERGROUP_CHECKBOX)
        #self.GroupBegin(GROUP_OPTIONS2, c4d.BFV_TOP, 1, 1)
        # Add Rad Group elements, and set to the current clip board
        self.AddCheckbox(CHKBOX_SCL_X, c4d.BFH_LEFT, initw=125, inith=8, name="X")
        self.AddCheckbox(CHKBOX_SCL_Y, c4d.BFH_LEFT, initw=125, inith=8, name="Y")
        self.AddCheckbox(CHKBOX_SCL_Z, c4d.BFH_LEFT, initw=125, inith=8, name="Z")
        self.GroupEnd()
        self.GroupEnd()

        self.AddSeparatorH(25,c4d.BFH_SCALEFIT)

        self.GroupBegin(GROUP_OK_CNL, c4d.BFH_LEFT, 3, 1)
        self.AddButton(BTN_OK, c4d.BFH_LEFT,initw=100, inith=10, name='Apply')
        self.AddButton(BTN_CNL, c4d.BFH_LEFT,initw=100, inith=10, name='Reset Values')
        self.AddButton(BTN_CNL2, c4d.BFH_LEFT,initw=100, inith=10, name='Cancel')
        self.GroupEnd()

        return True

    def check_gui_values(self):
        curPivType = self.GetInt32(RDO_GRP)
        tarPivType = self.GetInt32(RDO_GRP2)
        usePosX = self.GetBool(CHKBOX_POS_X)
        usePosY = self.GetBool(CHKBOX_POS_Y)
        usePosZ = self.GetBool(CHKBOX_POS_Z)
        useRotX = self.GetBool(CHKBOX_ROT_X)
        useRotY = self.GetBool(CHKBOX_ROT_Y)
        useRotZ = self.GetBool(CHKBOX_ROT_Z)
        useSclX = self.GetBool(CHKBOX_SCL_X)
        useSclY = self.GetBool(CHKBOX_SCL_Y)
        useSclZ = self.GetBool(CHKBOX_SCL_Z)

        return curPivType, tarPivType, usePosX,usePosY,usePosZ, useRotX, useRotY, useRotZ, useSclX, useSclY, useSclZ

    def update_align_position(self):
        # Get the current GUI values
        curPivType, tarPivType, usePosX,usePosY,usePosZ,useRotX,useRotY,useRotZ,useSclX, useSclY, useSclZ = self.check_gui_values()

        theTarget = self.linkBox.GetLink()
        _storedObjectB = theTarget
        _storedObjectBMg = theTarget.GetMg()
        _storedObjectBScale = theTarget.GetAbsScale()

        for i, curObj in enumerate(self.CurrentObjects):
            overide_specific_matrix_values(self.CurrentObjectsMg[i],_storedObjectBMg,
                                       self.CurrentObjectsScale[i],_storedObjectBScale,
                                       self.CurrentObjects[i],_storedObjectB,
                                       curPivType, tarPivType,
                                       usePosX, usePosY, usePosZ,
                                       useRotX, useRotY, useRotZ,
                                       useSclX, useSclY, useSclZ)
            # if tool is in axis mode 
            if self.axisMode:
                # if the current object is a point type object(Spline, Poly,... not Premative)
                if curObj.CheckType(c4d.Opoint):
                    curObj.Message(c4d.MSG_UPDATE)
                    newm = curObj.GetMg()

                    #print "This is the newm {0}".format(newm)
                    #print "This is pcount {0}".format(self.pcount)
                    for p in xrange(self.pcount[i]):
                        curObj.SetPoint(p,~newm*self.CurrentObjectsMg[i]*self.points[i][p])

                curObj.Message(c4d.MSG_UPDATE)
        c4d.EventAdd()

        return True    

    def EscTool(self):
        for i, curObj in enumerate(self.CurrentObjects):
            self.CurrentObjects[i].SetMg(self.CurrentObjectsMg[i])
        c4d.EventAdd()
        c4d.CallCommand(200000084)

    def SetObjectLink(self, myObject):
        self.linkBox.SetLink(myObject)

    def Command(self, id, msg):
        if id == BTN_OK:

            self.Close()
            c4d.CallCommand(200000084)
        # Close that shit
        elif id ==  BTN_CNL:
            # Set back to Original
            for i, item in enumerate(self.CurrentObjects):
                self.CurrentObjects[i].SetMg(self.CurrentObjectsMg[i])
            c4d.EventAdd()
            self.linkBox.SetLink(None)
            ##self.Close()

        elif id == BTN_CNL2:
            self.EscTool()

        # If anything is changed
        elif self.LayoutChanged(GROUP_POS):
            #print "Layout Changed"
            self.update_align_position()

        return True


class Aligner_Tool(plugins.ToolData):
    """Inherit from ToolData to create your own tool"""
    def __init__(self):
        self.CurrentObjects = None
        self.CurrentObjectsMg = None
        self.CurrentObjectsScale = None
        self.targetObject = dict(targetObject = None)
        self.BoolObject = False

        #self.enableLines = False
        self.tempLines = []
        self.hoverObject = None
        self.axisMode = False
        self.points = None
        self.pcount = None


    def InitTool(self,doc,data,bt):
        # Checking to see if doc has GetActiveObjects method, why? because for some reason throws an error on first
        # run, but work when you run the tool in the scene.
        hasAtter = getattr(doc,"GetActiveObjects",None)
        if callable(hasAtter):
            
            objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_SELECTIONORDER)
            if len(objects)<1:
                #print "Objects Less than one"
                gui.MessageDialog('Aligner must have one or more objects selected')
                c4d.CallCommand(200000084)
            else:
                ## supporting undo of all selected objects
                doc.StartUndo()
                for ob in objects:
                    doc.AddUndo(c4d.UNDOTYPE_CHANGE, ob)
                doc.EndUndo()

                # This is where I am storing the inital position of the selected objects
                MgList = []
                scaleList = []
                for o in objects:
                    newM = c4d.Matrix()
                    newM = o.GetMg()
                    MgList.append(newM)
                    scaleList.append(o.GetAbsScale())

                self.CurrentObjects = objects
                self.CurrentObjectsMg = MgList
                self.CurrentObjectsScale = scaleList
                self.targetObject["targetObject"] = objects[0]

                # quickly check if we are on axis mode rignt now... if yes...
                self.axisMode = doc.IsAxisEnabled()
                if self.axisMode:
                    thePoints = []
                    thePcounts = []
                    for o in objects:
                        if o.CheckType(c4d.Opoint):
                            thePoints.append(o.GetAllPoints())
                            thePcounts.append(o.GetPointCount())
                        else:
                            thePoints.append(None)
                            thePcounts.append(None)
        

                    self.points = thePoints
                    self.pcount = thePcounts
                    #print "set up points {0}".format(self.points)
                    #print "set uo Pcountg{0}".format(self.pcount)
        return True

    def FreeTool(self, doc, data):
        for spline in self.tempLines:
            spline.Remove()
        #return True

    def MouseInput(self, doc, data, bd, win, msg):
        mx = msg[c4d.BFM_INPUT_X]
        my = msg[c4d.BFM_INPUT_Y]

        vp = c4d.utils.ViewportSelect()
        selectedObject =vp.PickObject(bd, doc, int(mx), int(my), rad=int(10), flags=c4d.VIEWPORT_PICK_FLAGS_0)
        if selectedObject != []:
            for ob in selectedObject:
                # Checking to make sure you are not over the temp line and the object at same time
                if ob not in self.tempLines:
                    firstSelObj = ob
                    self.targetObject['targetObject'] = firstSelObj
                    self.BoolObject = True

                    self.myD.SetObjectLink(firstSelObj)
                    for spline in self.tempLines:
                        spline.Remove()
                    self.myD.update_align_position()

        return True

    def KeyboardInput(self, doc, data, bd, win, msg):
        key = msg.GetLong(c4d.BFM_INPUT_CHANNEL)
        cstr = msg.GetString(c4d.BFM_INPUT_ASC)
        if key==c4d.KEY_ESC:
            #do what you want
            #print "Hit Esc key"
            #c4d.CallCommand(1021385) # Rectangle Selection
            for spline in self.tempLines:
                spline.Remove()
            self.myD.EscTool()
            #return True to signal that the key is processed
            #return True
            
        return False

    def GetCursorInfo(self, doc, data, bd, x, y, bc):
        if bc.GetId() == -1:
            ## Check for an object if yes...
            vp = c4d.utils.ViewportSelect()
            op = vp.PickObject(bd, doc, int(x), int(y), rad=5, flags=c4d.VIEWPORT_PICK_FLAGS_0)

            if len(op)>0:
                ## IS IT NEW? YES... is  it a temp line?
                if op[0] != self.hoverObject:
                    if op[0] not in self.tempLines:
                        ## Kill old lines
                        for spline in self.tempLines:
                            spline.Remove()
                        ## Now you know that object is good set  hoverObject
                        self.hoverObject = op[0]
                        ## Get the hover object matrix position
                        v2Mg = self.hoverObject .GetMg()

                        ## loop through all the selected ojects and create a line
                        for o in self.CurrentObjects:
                            ## Get the object position
                            v1Mg = o.GetMg()

                            mySpline = c4d.SplineObject(2,c4d.SPLINETYPE_LINEAR)
                            mySpline.SetPoint(0,v1Mg.off)
                            mySpline.SetPoint(1,v2Mg.off)

                            self.tempLines.append(mySpline)

                            mySpline[c4d.ID_BASEOBJECT_USECOLOR]=2
                            color = c4d.Vector(1.0,1.0,0.0)

                            mySpline[c4d.ID_BASEOBJECT_COLOR]=color   

                            higestObjects = doc.GetObjects()
                            doc.InsertObject(mySpline,pred=higestObjects[-1])
                        c4d.EventAdd()

            else:
                for spline in self.tempLines:
                    spline.Remove()
                c4d.EventAdd()
                self.tempLines = []
                self.hoverObject = None

        return True

    def Draw(self, doc, data, bd, bh, bt, flags):
        return c4d.TOOLDRAW_HANDLES|c4d.TOOLDRAW_AXIS 

    def AllocSubDialog(self, bc):
        self.myD = SettingsDialog(self.CurrentObjects, self.CurrentObjectsMg, 
                                  self.CurrentObjectsScale,self.targetObject, 
                                  self.axisMode, self.points, self.pcount) 
        return self.myD

if __name__ == "__main__":
    bmp = bitmaps.BaseBitmap()
    dir, file = os.path.split(__file__)
    fn = os.path.join(dir, "res", "Aligner_Image.tif")
    bmp.InitWith(fn)
    plugins.RegisterToolPlugin(id=PLUGIN_ID, str="Aligner",
                                info=0, icon=bmp,
                                help="Align selected objects to a target object",
                                dat=Aligner_Tool())