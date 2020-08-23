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


#Scriptname & version: Cardboy0's Retroactive Beautifier - V.1.4 (I often forget to actually update this number so don't trust it)
#Author: Cardboy0 (https://twitter.com/cardboy0)
#Made for Blender 2.83



#############SETTINGS#############


first_frame = 1             #your chosen timerange that should be modified by this script.
last_frame  = 50


#####optional settings#####


use_animated_VGs = False    #Your "beauty modifiers" might use animated Vertex Groups (e.g. keyframed weights). For the script to work with those, you need to set this option to   True   . If disabled (set to    False   ) it will only use the weights of the current frame. 
#Disabling is recommended since this option can extremely slow the script down.

animated_VGs = []           #You can specify which VGs are animated to further decrease the slowdown. Only matters if use_animated_VGs = True . If the list is empty, all VGs will be used.
#Example: animated_VGs = ["Group.001", "SB-goal", "other VG"]



use_border_VG = False       #This is mainly intended for the results of my SPS script (https://github.com/Cardboy0/Shrinkwrap-Project-supporter) . Your deformed model will need a vertex group called "RB.border". This option will give all its vertices a weight of 1, except the ones of the bulge - but the most outer row of vertices of the bulge gets a weight of 1 as well. This allows you to get rid of the very sharp edges by using this VG for a Corrective Smooth modifier with like 300 Repeats, while leaving all other verts of the bulge in their original shape. Because this is hard to understand, the script will create one extra object after half of the frames are done, which will have the modifierd RB.border VG for the current frame, so you can view it in weight paint mode and see what it actually looks like.

border_thickness = 1        #the amount of outer rows of the bulge that get a weight of 1 in the "RB.border" VG. Default = 1




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
#V 1.4
#       - Got rid of the bug that slows down your blender session after finishing the script (when using high poly meshes for many frames).
#       - added use_border_VG as an optional option. This allows for better smoothing of SPS (another script by me) results.
#
#V 1.3.3
#       - Included an option that makes the script work with animated Vertex Groups (e.g. keyframed weights). Due to possible extreme slowness of this, it's disabled by default.
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
import math
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

#deletes objects and their meshes. If you just use the bpy.ops.delete(), the mesh will remain. This will mean that if you're script creates a new object each frame, you'll have one unassigned mesh for each frame when the script has finished and your session can become extremely slow.
#example: delete_objects([Obj_cube, Obj_sphere])
def delete_objects(object_list):
    for obj in object_list:
        mesh = obj.data
        D.objects.remove(obj)
        D.meshes.remove(mesh)
        
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

    #we must make sure that only vertex selection is possible in edit mode, otherwise problems will appear
    O.object.mode_set_with_submode(mode='EDIT',  mesh_select_mode = {"VERT"} ) 
    O.object.mode_set(mode='OBJECT')

    
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

    #To get the actual, final weights (with all modifiers) of Obj_defo to Obj_working, we'll transfer them with a Data Transfer modifier and apply it.
    for i in Obj_defo.vertex_groups:
        Obj_working.vertex_groups.new(name = i.name)
    Mod_datatransfer = Obj_working.modifiers.new("transfer VGs","DATA_TRANSFER")
    Mod_datatransfer.object = Obj_defo
    Mod_datatransfer.use_vert_data = True
    Mod_datatransfer.data_types_verts = {'VGROUP_WEIGHTS'}
    Mod_datatransfer.vert_mapping = 'TOPOLOGY'
    apply_modifiers(Obj_working)


    
    #Giving Obj_working all the "beautifying" mods.
    select_objects([Obj_defo, Obj_working])
    bpy.ops.object.make_links_data(type='MODIFIERS')    #deletes any present modifiers, but at least it doesn't delete referenced non-existent VGs
    for i in Obj_working.modifiers:
        if not i.name.startswith("RB."):
            Obj_working.modifiers.remove(i)
        else:
            i.show_viewport = True
    
    
    
    if use_border_VG == True:
        
        #needed for "resetting" VGs later
        all_vert_indices = []
        for i in Obj_defo_mdd.data.vertices:
            all_vert_indices += [i.index]

        for i in range(first_frame, last_frame + 1):
            C.scene.frame_set(i)
            print('current frame:', i)
            deformed_verts = []
            
            
            #creating static duplicates since shapekeys alone dont change vertex coordinates
            select_objects([Obj_orig_mdd])
            O.object.object_duplicate_flatten_modifiers()
            Obj_t_orig = C.object
            select_objects([Obj_defo_mdd])
            O.object.object_duplicate_flatten_modifiers()
            Obj_t_defo = C.object
            
            
            #comparing vertices of both objects to see which ones have been deformed
            for e in range(len(Obj_t_orig.data.vertices)):
                for f in [0,1,2]:
                    if not math.isclose(Obj_t_orig.data.vertices[e].co[f], Obj_t_defo.data.vertices[e].co[f], abs_tol=0.00001):
                        deformed_verts += [e]
                        break
            

            
            #Obj_working will get a new VG for each frame
            VG_new = Obj_working.vertex_groups.new(name = "RB_bord_frame_" + str(i))
            #for some reason creating new VGs sometimes already has certain areas assigned with a weight of 1, so we have to remove all verts at first to be sure
            VG_new.remove(all_vert_indices)
            VG_new.add(deformed_verts, 1, "ADD")
            

            select_objects([Obj_working])
            O.object.mode_set(mode='EDIT')
            Obj_working.vertex_groups.active = VG_new
            O.mesh.select_all(action='DESELECT')
            O.object.vertex_group_select()
            for e in range(border_thickness):
                O.mesh.select_less()
            C.scene.tool_settings.vertex_group_weight = 1
            
            mode = "INNER_INVERT"
            if mode == "INNER":
                O.object.vertex_group_assign()
                O.mesh.select_all(action='INVERT')
                O.object.vertex_group_remove_from()
            elif mode == "INNER_INVERT":
                O.object.vertex_group_remove_from()
                O.mesh.select_all(action='INVERT')
                O.object.vertex_group_assign()
            
            O.object.mode_set(mode='OBJECT')    
    
            if i != int((last_frame-first_frame)/2+first_frame):
                delete_objects([Obj_t_defo, Obj_t_orig])
            else:
                delete_objects([Obj_t_orig])
                Obj_t_defo.name = "border_VG for frame " + str(i) +" (example)"
                select_objects([Obj_working, Obj_t_defo])
                O.object.vertex_group_copy_to_selected()
                for e in Obj_t_defo.vertex_groups:
                    if e != Obj_t_defo.vertex_groups.get("RB_bord_frame_" + str(i)):
                        Obj_t_defo.vertex_groups.remove(e)
                Obj_t_defo.vertex_groups[0].name = "RB.border"
    
        VG_border = Obj_working.vertex_groups.get("RB.border")
    
    
     
    #Beauty mods might use VGs whose weights change with frames. To "update" those weights, we'll have to transfer those specified vertex groups with a Data Transfer modifier (IF ENABLED). It needs to be the first modifier in the stack. It also overwrites all exisiting weights.
    if use_animated_VGs == True:
        #adds one data transfer mod for all VGs
        if animated_VGs == []:
            Mod_datatransfer = Obj_working.modifiers.new("transfer VGs","DATA_TRANSFER")
            Mod_datatransfer.object = Obj_defo
            Mod_datatransfer.use_vert_data = True
            Mod_datatransfer.data_types_verts = {'VGROUP_WEIGHTS'}
            Mod_datatransfer.vert_mapping = 'TOPOLOGY'
            select_objects([Obj_working])
            for i in range(len(Obj_working.modifiers)):
                O.object.modifier_move_up(modifier = Mod_datatransfer.name)
        #adds several data transfer mods for each listed VG
        else:
            for i in animated_VGs:
                Mod_datatransfer = Obj_working.modifiers.new("transfer VG " + i,"DATA_TRANSFER")
                Mod_datatransfer.object = Obj_defo
                Mod_datatransfer.layers_vgroup_select_src = i       #changed before use_vert_data = True so that it doesn't waste calculation time by transfering all VGs first bc of default.
                Mod_datatransfer.use_vert_data = True
                Mod_datatransfer.data_types_verts = {'VGROUP_WEIGHTS'}
                Mod_datatransfer.vert_mapping = 'TOPOLOGY'
                select_objects([Obj_working])
                for e in range(len(Obj_working.modifiers)):
                    O.object.modifier_move_up(modifier = Mod_datatransfer.name)

    Obj_beauty.name   = "beautified result"
    Obj_defo_mdd.name = "mdd defo"
    Obj_orig_mdd.name = "mdd orig"


#the actual rebinding stuff for each frame
for i in range(first_frame, last_frame + 1):
    C.scene.frame_set(i)
    print('current frame:', i)
        
    with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):

        if use_border_VG == True:
            Obj_working.vertex_groups.remove(VG_border)
            VG_border = Obj_working.vertex_groups.get("RB_bord_frame_" + str(i))
            VG_border.name = "RB.border"

    
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
        delete_objects([Obj_temp])
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
    delete_objects([Obj_orig_mdd, Obj_defo_mdd, Obj_working])

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
