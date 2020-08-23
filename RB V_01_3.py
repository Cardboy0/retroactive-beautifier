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


#Scriptname & version: Cardboy0's Retroactive Beautifier - V.1.3 
#Author: Cardboy0 (https://twitter.com/cardboy0)
#Made for Blender 2.83



#############SETTINGS#############


first_frame = 1             #your chosen timerange that should be modified by this script.
last_frame  = 50





#################################
###########DESCRIPTION###########

#You can download the newest version of this scipt at https://github.com/Cardboy0/retroactive-beautifier
#Guide (NSFW!) at https://docs.google.com/document/d/1rpJIQqvXcGL9UN-JYzqRKVHk8xaMxgCKM0UYLyqDW_A/edit#heading=h.prpv8opcw7ou


#What this script is for:
#You have an animated object with an ugly deformation, e.g. a moving bulge on human skin. You want to use modifiers like "Corrective Smooth" to make that deformation look better. But these modifiers can only use one shape of your object as a reference (Corrective Smooth for instance uses the shape of your model with all shapekeys and modifiers disabled). When you use this script however, for each frame it will give those modifiers the shape of the current frame - without the deformation - as a reference. Thus if you don't have any deformations, your object will look exactly like it did before.

#The final result will be animated solely through keyframed shapekeys.


#################################
########QUICK-START GUIDE########

#1. In your preferences, enable the following 2 Add-ons:
#       "Corrective Shape Keys"
#       "NewTek MDD format"
#   (Just type their names into the searchbar and check the box)
#2. Have two versions of the same object: One copy showing the original animation, one copy showing the deformed animation
#3. Give the deformed object a "Corrective Smooth" modifier with default properties. Rename it to "RB.Corrective Smooth". (Script identifies modifiers with "RB." at the start)
#4. Head over to the "Scripting" Workspace inside your Blender project.
#5. In the text editor that's in the middle, open this script.
#6. Inside the script at the top there's a settings section. Change first_frame to the first frame of your animation, and last_frame to the last one.
#7. Select the two objects. The original one needs to be the active object.
#8. Save your file in a new folder.
#9. In the text editor at the top right, press the "Run Script" (arrow) button.
#10. Wait for it to finish. (If you want to see the progress, open the Blender System Console)

#If you get an error, make sure that you undo the "Run Script" action in your Undo History. Otherwise things could get messy.

#################################
#############CHANGELOG###########
#V 1.3
#       - Completely rewrote the script. Maybe I forgot listing some things here.
#       - Neither objects need to be animated in the "mdd format"-way anymore, the script does that for you.
#       - ("beauty mods") The mods this script should work with (e.g. Corrective Smooth)...
#           + need to be renamed: At the start of their name, a "RB." is required ("modname" => "RB.modname").
#           + need to be on the deformed object, not the original one
#       - Mods like "Laplacian Deform" now get rebound every frame by default (if they're a "beauty mod")
#       - Vertex Groups of the deformed object are taken into account while this script is running, which means your "beauty mods" can reference them no problem.

#V 1.1.3
#       - Fixed the bug that prevented this script from working.
#       - Result object will now appear in the collection of the "calc" object.
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
    if object_list == [] and active_object == None:
        return "no objects to select"
    for i in object_list:
        i.select_set(True)
    if active_object == None:
        C.view_layer.objects.active = object_list[0]
    else:
        C.view_layer.objects.active = active_object        
        
#links and unlinks specified objects to the specified collections. To prevent bugs the objects should all share the same collections
#example: link_objects(bpy.context.selected_objects, bpy.context.scene.collection.children['New_Collection'], [bpy.context.scene.collection.children['Old_Collection']])
def link_objects(objects, link_to, unlink_to = []): #unlink_to needs to be a list (collections to unlink), None (unlink no collection), or not be specified at all (unlink all collections). link_to only uses one collection, so no list.
    if unlink_to == []:
        unlink_to = objects[0].users_collection    
    elif unlink_to == None:
        unlink_to = []
    
    for i in objects:
        for x in unlink_to:
            x.objects.unlink(i)
        link_to.objects.link(i)    
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

    
    #assigning objects to variables
    for i in C.selected_objects:
        if i == C.view_layer.objects.active:
            Obj_orig = i
        else:
            Obj_defo = i
    beautymods = []
    for i in Obj_defo.modifiers:
        if i.name.startswith("RB."):
            beautymods += [[i, i.show_viewport]] #to safe their viewport visibility for resetting later
            i.show_viewport = False #remember to unset later again

    
    #creating copies of the two original objects that are only animated through keyframed shapekeys
    select_objects([Obj_orig])
    O.export_shape.mdd (filepath = target_file, frame_start = first_frame, frame_end = last_frame)
    bpy.ops.object.object_duplicate_flatten_modifiers()
    Obj_orig_mdd = C.object
    O.import_shape.mdd(filepath=target_file, frame_start = first_frame)

    select_objects([Obj_defo])
    O.export_shape.mdd (filepath = target_file, frame_start = first_frame, frame_end = last_frame)
    bpy.ops.object.object_duplicate_flatten_modifiers()
    Obj_defo_mdd = C.object
    O.import_shape.mdd(filepath=target_file, frame_start = first_frame)

    
    #these objects are needed later, but just need to have the same topology as the other objects.
    bpy.ops.object.object_duplicate_flatten_modifiers()
    Obj_working = C.object
    bpy.ops.object.duplicate()
    Obj_beauty  = C.object


    #for the datatransfer mod later on
    for i in Obj_defo.vertex_groups:
        Obj_working.vertex_groups.new(name = i.name)

    
    #Giving Obj_working all the "beautifying" mods.
    select_objects([Obj_defo, Obj_working])
    bpy.ops.object.make_links_data(type='MODIFIERS')    #deletes any present modifiers, but at least it doesn't delete referenced non-existent VGs
    for i in Obj_working.modifiers:
        if not i.name.startswith("RB."):
            Obj_working.modifiers.remove(i)
        else:
            i.show_viewport = True

    #Beauty mods can need vertex groups, so we use a Data Transfer modifier to transfer the vertex groups of the original to this object. It needs to be the first modifier in the stack.
    Mod_datatransfer = Obj_working.modifiers.new("transfer VGs","DATA_TRANSFER")
    Mod_datatransfer.object = Obj_defo
    Mod_datatransfer.use_vert_data = True
    Mod_datatransfer.data_types_verts = {'VGROUP_WEIGHTS'}
    Mod_datatransfer.vert_mapping = 'TOPOLOGY'
    select_objects([Obj_working])
    for i in range(len(Obj_working.modifiers)):
        O.object.modifier_move_up(modifier = Mod_datatransfer.name)

    Obj_beauty.name   = "beautified result"
    Obj_defo_mdd.name = "mdd defo"
    Obj_orig_mdd.name = "mdd orig"


#the actual rebinding stuff for each frame
for i in range(first_frame, last_frame + 1):
    C.scene.frame_set(i)
    print('current frame:', i)
        
    with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):    
        Obj_working.shape_key_clear()
        
        #changing the Basis shape to the current shape of Obj_orig
        select_objects([Obj_working, Obj_orig_mdd])
        bpy.ops.object.join_shapes()
        Obj_working.active_shape_key_index = 0
        O.object.shape_key_remove(all=False)
        
        
        #rebinding any binding mods to this current shape
        #the deform modifiers that support binding (Corrective Smooth, Laplacian Deform, Surface Deform and Mesh Deform) all have a different operators for the binding so I had to write this ugly if-thing you see here.
        for e in Obj_working.modifiers:
            if e.type == 'CORRECTIVE_SMOOTH':
                if e.rest_source == "BIND":
                    O.object.correctivesmooth_bind(modifier = e.name)
                    if e.is_bind == False:      #if it was unbound before, it's now bound, if it was already bound it has to be binded again since we unbound it (the binding-op only toggles between bind and unbind)
                        bpy.ops.object.correctivesmooth_bind(modifier = e.name)
            elif e.type == 'LAPLACIANDEFORM':
                O.object.laplaciandeform_bind(modifier = e.name)
                if e.is_bind == False:
                    O.object.laplaciandeform_bind(modifier = e.name)    
            elif e.type == 'MESH_DEFORM':
                O.object.meshdeform_bind(modifier = e.name)
                if e.is_bound == False:     #notice that with this and the next modifier it's "is_bound" instead of "is_bind"
                    O.object.meshdeform_bind(modifier = e.name)
            elif e.type == 'SURFACE_DEFORM':
                O.object.surfacedeform_bind(modifier = e.name)
                if e.is_bound == False:
                    O.object.surfacedeform_bind(modifier = e.name )
        
        
        #adding a shapekey with the current shape of Obj_defo
        select_objects([Obj_working, Obj_defo_mdd])
        bpy.ops.object.join_shapes()
        Obj_working.data.shape_keys.key_blocks[1].value = 1
        
        
        #Mods should have "beautified" the shape of Obj_working now, so it'll be transfered as a shapekey to the final object.
        select_objects([Obj_working])
        bpy.ops.object.object_duplicate_flatten_modifiers()
        Obj_temp = C.object
        select_objects([Obj_beauty, Obj_temp])   #apparentely join_shapes doesn't work for all mods! Thus, always create duplicate_for_editing first instead
        bpy.ops.object.join_shapes()
        select_objects([Obj_temp])
        O.object.delete(use_global=False)
        SK_new = Obj_beauty.data.shape_keys.key_blocks[-1]
     
        #naming the new shapekey: For the possibility that you want to join your result with another object later on (which also is animated through mdd), the shapekeys have to have the same names, so this script tries to name them the same way mdd does by default when importing.
        if i < 1000:
            frame_current = "0" + str(i - 1)
            if i < 100:
                frame_current = "0" + frame_current
                if i < 10:
                    frame_current = "0" + frame_current #if frame_current was e.g. "7", it's now "0007"
        SK_new.name = 'frame_'+frame_current
        #to see the shapekeys animated, they have to have a value of 1 for their respective frame, but a value of 0 all the other time.
        for e in [-1,0,1]:          
            C.scene.frame_set(i + e)
            if e != 0:
                SK_new.value = 0
            else:
                SK_new.value = 1
            SK_new.keyframe_insert(data_path = 'value')
    
with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):    
    select_objects([Obj_orig_mdd, Obj_defo_mdd, Obj_working])
    O.object.delete(use_global=False)

    #linking objs to collection of Obj_defo
    link_objects([Obj_beauty], Obj_defo.users_collection[0])
    
    Obj_orig.hide_set(True)
    Obj_defo.hide_set(True)
    select_objects([Obj_beauty])

    #resetting stuff
    for i in beautymods:
        i[0].show_viewport = i[1]
    C.scene.frame_set(default_frame)
    
print('\n\n'+2*print_symbol_asterik+'\nScript finished!\n\n'+2*print_symbol_asterik+'\n\n\n\n\n\n')