# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


#Scriptname & version: Cardboy0's Retroactive Beautifier - V.1.1 
#Author: Cardboy0 (https://twitter.com/cardboy0)
#Made for Blender 2.82



#############SETTINGS#############


first_frame = 1             #your chosen timerange that should be modified by this script.
last_frame  = 50




#####optional settings#####

mods_bind_each_frame = ['Your_modifier_name_here','something like CorrectiveSmooth.001','maybe another one?','CorrectiveSmooth'] 
#If your modifier has a fat "bind" button. Certain Deform modifiers, like "Laplacian Deform", can be ***bound*** to some specific shape of your object. That bind stays the same for the whole time, except when you put the name of your modifier in the list above. Then it will be rebound every frame. You probably want that.



#################################
###########DESCRIPTION###########

#You can download the newest version of this scipt at https://github.com/Cardboy0/retroactive-beautifier

#What this script is for: You have an animated object. You have a duplicate of that object, but with a deformation: for instance a bulge. You want to *only* smoothen out the bulge and keep everything else, including the animation, the way it looks like on the original animated object. That's what this script can do. It's mainly made to clean up the result of the https://github.com/Cardboy0/Cardboy0s-SACS script.


#################################
########QUICK-START GUIDE########

#1. In your preferences, enable the following 2 Add-ons:
#       "Corrective Shape Keys"
#       "NewTek MDD format"
#   (Just type their names into the searchbar and check the box)
#2. Have two animated objects: the original one, and the deformed one.
#3. The animation of the deformed object needs to be completely turned into shapekeys. If you're using a result of the SACS script, that already is the case; if not, see the additional guide below for using the .mdd format
#4. Give the deformed object a "Corrective Smooth" modifier with default properties.
#5. Head over to the "Scripting" Workspace inside your Blender project.
#6. In the text editor that's in the middle, open this script.
#7. Inside the script at the top there's a settings section. Change first_frame to the first frame of your animation, and last_frame to the last one.
#8. Toggle the System Console in the "Window"-settings of your Blender file. This new window will display the progress of the script.
#9. Select the two objects. The original one needs to be the active object.
#10. Save your file in a new folder.
#11. In the text editor at the top right, press the "Run Script" button.
#12. Check the progress in the console window, and wait for it to finish.

#If you get an error, make sure that you undo the "Run Script" action in your Undo History. Otherwise things could get messy.


#####using .mdd format#####
# This is only important if you don't use a result of the SACS script.
# Objects can show many kinds of animations through shapekeys, transformations, modifiers etc. Using the .mdd Format, these animations can be converted completely into keyframed shapekeys; one shapekey for each frame.

#1. In your preferences, enable the following Add-on:
#       "NewTek MDD format"
#2. Select your animated object
#3. Export it as an .mdd (Lightwave Point Cache)
#       Don't forget to choose the right Start and End frame when exporting in the properties bar at the right.
#4. Duplicate your animated object.
#5. Delete all shapekeys of the duplicate
#6. Deal with all the modifiers from top to bottom:
#       If it's visible in viewport, apply it
#       If it's hidden or disabled, delete it
#7. Delete all keyframes of the duplicate
#8. Clear all transformations
#9. Select the duplicate
#10. Import the previously exported .mdd file again.

#The duplicate should now show the same animation as the original one, only that it's only being animated through shapekeys.
#If the duplicate looks all distorted, it is likely that the total vertex amount changed between exporting and importing. If you had a "Subdivision Surface" modifier enabled while exporting, those additional vertices will be saved in the .mdd as well. If you then delete the modifier instead of applying it, it will have less vertices than there are saved in the .mdd, and Blender doesn't know what to do when it tries to import it.




#################################
#############CHANGELOG###########

#V 1.1
#       - Added actual information text being shown in the console
#       - Completely rewrote the text at the beginning of the script.
#           + Added a Changelog
#       - The original object does no longer need to be animated through shapekeys alone, you dont have to change it in any way. The deformed one still does however.
#       - The visual modifiers (like "Corrective Smooth") now need to be added to the deformed object instead of the original one.

#V 1.0 
#       - Base version.





#########################################################################
#########################Actual script begin#############################
#########################################################################
import bpy
import os
import contextlib

print('##########################################################################')
print('script "Retroactive Beautifier" begin')
print('##########################################################################')

C = bpy.context
D = bpy.data
O = bpy.ops



##############################Functions##################################
#lets you select a list of objects (need to input the actual classes instead of their names), and also optionally choose the object you want to be active. By default it sets the first item in the list as active. The optional active object doesn't have to be in the list to be set as active, but then it still won't be selected.
#will deselect all other objects
#example: select_objects([Suzanne,Cube,Suzanne.001],Suzanne.004)
def select_objects(object_list, active_object = None):
    O.object.select_all(action='DESELECT')
    for i in object_list:
        i.select_set(True)
    if active_object == None:
        C.view_layer.objects.active = object_list[0]
    else:
        C.view_layer.objects.active = active_object

#Deletes the basis shapekey of the specified object, allowing the next shapekey in the stack to be the new basis. Notice that it will look like the new basis had a value of 1 before. If no object is specified, it will use the currently active object.
def delete_basis_SK(s_object = None):
    if s_object != None:
        select_objects([s_object])
    orig_active_SK = C.object.active_shape_key_index
    C.object.active_shape_key_index = 0
    O.object.shape_key_remove(all=False)
    C.object.active_shape_key_index = orig_active_SK - 1
    
#applies the specified modifiers (use the actual names of the modifiers) of the specified object. The order in which the modifiers are applied is equal to their order in the list -> the first one gets applied first. It uses a context-override so it doesn't select/deselect any objects. Setting invert to True means that it will apply all modifiers of the object that are *not* in the given modifier list, however it will take the default mod-stack order. Choosing an empty list means it will apply all modifiers. If delete_hidden is set to True, it will delete, instead of apply, a modifier if it is set to hidden.
#example: apply_modifiers('Cube.001',["Wireframe.001","Subdivision"])
def apply_modifiers(object, modifier_list = [], invert = False, delete_hidden = False):                    #had a problem with the context override, for future reference: if you want to do stuff with "active_object", you also have to change "object" to that object.
    override = C.copy()
    override['active_object'] = object
    override['object']= object
    if modifier_list == []:
        modifier_list = list(object.modifiers.keys())
    if invert == True:
        h_modifier_list = list(object.modifiers.keys())
        for i in modifier_list:
            if i in h_modifier_list:
                h_modifier_list.remove(i)
        modifier_list = h_modifier_list
    if delete_hidden == True:
        for i in modifier_list:
            if i in object.modifiers.keys():
                if object.modifiers[i].show_viewport == True:
                    try:
                        O.object.modifier_apply(override, apply_as='DATA', modifier = i)
                    except RuntimeError:
                        print("OOPS! MODIFIER", i, "IS DISABLED! IT WILL BE DELETED") #trying to apply a disabled modifiier leads to an error message, but I didn't figure out how to check if it's disabled. Thus, we'll have to deal with the error instead.
                        print("ERROR TYPE IS", sys.exc_info()[0])
                        O.object.modifier_remove(modifier = i)   
                elif object.modifiers[i].show_viewport == False:
                    O.object.modifier_remove(modifier = i)
    elif delete_hidden == False:
        for i in modifier_list:
            if i in object.modifiers.keys():
                O.object.modifier_apply(override, apply_as='DATA', modifier = i)
#########################################################################


#########################################################################
print_symbol_hash = '##########################################################################\n'
print_symbol_asterik = '*****************************************************************\n'

default_frame = C.scene.frame_current

print('preparing...')
with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):  #this prevents used functions printing statements in the system console by themselves, which are useless to the user and make it seem more chaotic.


    #create the mdd file / the filepath.
    blend_file_path = D.filepath 
    directory = os.path.dirname(blend_file_path)
    target_file = os.path.join(directory, 'you can delete this.mdd')


    ###############the following section is to convert the original animation object into an mdd animated one. Also, the modifiers from the calc object will be transfered to the new mdd object.
    O.object.duplicate()

    #assigning the 2 duplicate objects to variables.
    original_model = C.object
    calc_model = C.selected_objects[1]
    print('names:',original_model.name, calc_model.name)

    #exporting and importing the .mdd files as well as applying/deleting modifiers and changing VGroups

    #exporting and applying mods                                                         
    select_objects([original_model])  
    O.export_shape.mdd (filepath = target_file, frame_start = first_frame, frame_end = last_frame)
    select_objects([original_model])  
    original_model.shape_key_clear()     #modifiers can't be applied when the object has shapekeys
    apply_modifiers(object = original_model, delete_hidden = True)
    O.anim.keyframe_clear_v3d() #clears all transformation keyframes of the object (Object -> animation -> clear keyframe). We might have to delete all keyframes though.
    O.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    O.object.transform_apply(location=True, rotation=True, scale=True)

    ###importing
    select_objects([original_model])
    O.import_shape.mdd(filepath=target_file, frame_start = first_frame)


    ###giving the original_model the visual modifiers of the calc_model, and deleting them from the calc_model. The only reason we move them from one object to the other one is that these lines are being added new to the RB script and the original version required the modifiers on the original_model. I could change that, but dont want to right now.
    select_objects([calc_model, original_model])
    O.object.make_links_data(type='MODIFIERS')
    select_objects([calc_model])
    for mods in calc_model.modifiers:
        O.object.modifier_remove(modifier = mods.name)
        
    select_objects([original_model, calc_model])
    ###############



    #assigning the selected objects to variables
    for i in C.selected_objects:
        if i == C.view_layer.objects.active:
            Original = i
        else:
            Baked = i 

    select_objects([Original])
    O.object.duplicate()
    CopyOriginal = C.object #to prevent us seriously messing something up, we use a copy of the main_anim object instead of the original for the stuff this script does, and delete it at the end again.


    #this script depends on the objects shapekeys and their order instead of the actual keyframes to know what to do for each frame, so it "refreshes" them once by exporting/importing mdd itself.
    for i in C.object.modifiers:
        i.show_viewport = False    #when exporting the mdd will save the exact way the object *looks* like in the viewport, so we need to disable all mods first
    O.export_shape.mdd(filepath=target_file, frame_start=first_frame, frame_end=last_frame, fps=C.scene.render.fps, use_rest_frame=False)
    O.object.shape_key_remove(all=True)
    O.object.transform_apply(location=True, rotation=True, scale=True) #applying or clear doesn't matter, the transform values just have all to be default.
    O.import_shape.mdd(filepath=target_file, frame_start = first_frame, frame_step=1) #first shapekey (after basis) is now keyframed to 1 at first_frame


    #Instead of importing the calc animation as mdd as well, its animation will be shown with a mesh cache modifier on the same object that had the main_anim mdd imported. So one animation is shown through keyframed shapekeys, the other one through the mesh cache mod.
    select_objects([Baked])
    for i in C.object.modifiers:
        i.show_viewport = False
    O.export_shape.mdd(filepath=target_file, frame_start=first_frame, frame_end=last_frame, fps=C.scene.render.fps, use_rest_frame=False)
    select_objects([CopyOriginal])
    Mesh_Cache = CopyOriginal.modifiers.new(name="Mesh Cache", type='MESH_CACHE')
    Mesh_Cache.cache_format = 'MDD'
    Mesh_Cache.filepath = target_file
    Mesh_Cache.frame_start = first_frame
    Mesh_Cache.frame_scale = 1.0 #am not sure about that value but still set it to 1 just to be safe

    #duplicate_flatten() - which is an operator of the "Corrective Shape Keys" add-on and will be used later - also takes into account how an object looks, but creates a new object with that new topology instead. So we need to see that modified topology in the viewport.
    for i in C.object.modifiers:
        i.show_viewport = True 

    #needs to be the first in stack order since stuff like corrective smooth doesnt take lower modifiers into account
    for i in range(len(list(CopyOriginal.modifiers))):
        O.object.modifier_move_up(modifier=Mesh_Cache.name)

    #mute all shapekeys. We only need the shapekeys to change the Basis-shapekey each frame to give modifiers like corrective smooth a new reference to work with, even when muted the new base will look like it had a value of 1.
    for i in CopyOriginal.data.shape_keys.key_blocks:     
                        i.mute = True

    #clean up the mods_bind_each_frame - list to only include modifier names that the object actually has.
    #to compare them we need to make a list of the actual modifiers that only has the names of them though.
    mods_actual = []
    for i in CopyOriginal.modifiers:
        mods_actual = mods_actual + [i.name]
    mods_copy = list(mods_bind_each_frame) #if you don't use the list argument they're both linked to the same list, which messes up the next for-loop as it removes elements while looping
    for i in mods_copy:
        if i not in mods_actual:
            print("modifier",'"'+i+'"',"not found; ignoring it")
            mods_bind_each_frame.remove(i)

       
    #getting the types to choose the right operators later on, they will have the same indices as the actual names of the modifiers in the mod list.
    modifier_types = []
    for i in mods_bind_each_frame:
        modifier_types = modifier_types + [CopyOriginal.modifiers[i].type]


    frame_current_overall = first_frame

print('')

#this is the stuff that happens each frame
for x in range(last_frame - first_frame + 1):
    print('current frame:', frame_current_overall)
    with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):
        C.scene.frame_set(frame_current_overall)
        delete_basis_SK(CopyOriginal)
        
        #the deform modifiers that support binding (Corrective Smooth, Laplacian Deform, Surface Deform and Mesh Deform) all have a different operators for the binding so I had to write this ugly if-thing you see here.
        Mesh_Cache.show_viewport = False #the mesh-cache mod is the first one in the stack by default, meaning that if we don't disable it prior to binding it will count towards the bind as well.
        index = -1
        for i in modifier_types:
            index = index + 1
            if modifier_types[index] == 'CORRECTIVE_SMOOTH':
                O.object.correctivesmooth_bind(modifier=mods_bind_each_frame[index])
                if CopyOriginal.modifiers[mods_bind_each_frame[index]].is_bind == False:      #if it was unbound before, it's now bound, if it was already bound it has to be binded again since we unbound it (the binding-op only toggles between bind and unbind)
                    bpy.ops.object.correctivesmooth_bind(modifier=mods_bind_each_frame[index])
            elif modifier_types[index] == 'LAPLACIANDEFORM':
                O.object.laplaciandeform_bind(modifier=mods_bind_each_frame[index])
                if CopyOriginal.modifiers[mods_bind_each_frame[index]].is_bind == False:
                    O.object.laplaciandeform_bind(modifier=mods_bind_each_frame[index])    
            elif modifier_types[index] == 'MESH_DEFORM':
                O.object.meshdeform_bind(modifier=mods_bind_each_frame[index])
                if CopyOriginal.modifiers[mods_bind_each_frame[index]].is_bound == False:     #notice that with this and the next modifier it's "is_bound" instead of "is_bind"
                    O.object.meshdeform_bind(modifier=mods_bind_each_frame[index])
            elif modifier_types[index] == 'SURFACE_DEFORM':
                O.object.surfacedeform_bind(modifier=mods_bind_each_frame[index])
                if CopyOriginal.modifiers[mods_bind_each_frame[index]].is_bound == False:
                    O.object.surfacedeform_bind(modifier=mods_bind_each_frame[index])
        Mesh_Cache.show_viewport = True
        
        
        O.object.object_duplicate_flatten_modifiers()
        Temp_Dupl = C.object
        if frame_current_overall == first_frame:
            O.object.duplicate()
            Applied_Dupl = C.object #since the modifiers basically get applied, to transfer them as shapekeys the new object also has to have that same topology. So we just use the first created temp_duplicate as the one where everything else going to be imported on.
            select_objects([Temp_Dupl])
            
        O.object.shape_key_add(from_mix=False)
        Temp_Dupl.active_shape_key_index = 0    #to be able to transfer the shape/(-key) of this duplicate to another object as a shapekey it of course has to have one in the first place.
        select_objects([Applied_Dupl,Temp_Dupl])
        #O.object.shape_key_transfer()   #important: transfering instead of joining only transfers the changes from basis to shapekey, meaning if there's no change in shape, the shapekey is gonna be basically empty.
        bpy.ops.object.join_shapes() 
        Applied_Dupl.active_shape_key_index = -1 #the last added shapekey is gonna be the last one in the stack
        
        #naming the new shapekey: For the possibility that you want to join your result with another object later on (which also is animated through mdd), the shapekeys have to have the same names, so this script tries to name them the same way mdd does by default when importing.
        frame_current = str(x)
        if x < 1000:
            frame_current = "0" + frame_current
            if x < 100:
                frame_current = "0" + frame_current
                if x < 10:
                    frame_current = "0" + frame_current #if frame_current was e.g. "7", it's now "0007"
        C.object.data.shape_keys.key_blocks[-1].name = 'frame_'+frame_current
        
        #to see the shapekeys animated, they have to have a value of 1 for their respective frame, but a value of 0 all the other time.
        for i in [-1,0,1]:          
            C.scene.frame_set(frame_current_overall + i)
            if i != 0:
                C.object.data.shape_keys.key_blocks[-1].value = 0
            else:
                C.object.data.shape_keys.key_blocks[-1].value = 1
            C.object.data.shape_keys.key_blocks[-1].keyframe_insert(data_path = 'value')
        C.scene.frame_set(frame_current_overall)
        
        select_objects([Temp_Dupl])
        O.object.delete(use_global=False)
        frame_current_overall = frame_current_overall + 1


with open(os.devnull, "w") as f, contextlib.redirect_stdout(f): 
    select_objects([CopyOriginal, calc_model, original_model])
    O.object.delete(use_global=False)    
    #Original.hide_viewport = True
    #Baked.hide_viewport = True        #disabled for now since it does hide them, but to unhide them you have to set hide_viewport to True in the console yourself again if you want to see them, since using the hide button doesn't work for some reason.
    select_objects([Applied_Dupl])
    Applied_Dupl.name = "beautified result"
        
        
    C.scene.frame_set(default_frame)

print('\n\n'+2*print_symbol_asterik+'\nScript finished!\n\n'+2*print_symbol_asterik+'\n\n\n\n\n\n')
