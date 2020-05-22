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


#Scriptname & version: Cardboy0's Retroactive Beautifier - V.1.0.0 
#Author: Cardboy0 (https://www.deviantart.com/cardboy0)
#Made for Blender 2.82



#############################################################
########################user input:##########################
#############################################################


frame_start = 100             #your chosen timerange that should be modified by this script.
frame_end   = 140


#####optional:

mods_bind_each_frame = ['Your_modifier_name_here','something like CorrectiveSmooth.001','maybe another one?','CorrectiveSmooth'] 
#certain Deform modifiers like Laplacian Deform can be bound to some specific shape of your object. That bind stays the same for the whole time, except when you put the name of your modifier in the list above. Then it will be rebound every frame. You probably want that.


#############################################################
#############################################################
#############################################################

################ABOUT THIS SCRIPT:

#The purpose of this script is to apply modifiers of an animated object for each frame and then transfer all these new shapes to the final result. The modifiers in mind are the deform modifiers, especially: Corrective Smooth, Laplacian Deform, Mesh Deform and Surface Deform (I didnt really test all of them yet though so some might not work right now). I'm gonna use Corrective Smooth as an example: Corrective Smooth smoothens out deformations of your object caused by shapekeys or modifiers that are higher in the mod-stackorder. But the basis shape, which is used as the reference (how the object *should* look like) doesn't change with frames, it stays the same. Let's say you have a plane that has a Wave mod and does wave things nice and good. You also added a Vertex Weight Proximity mod in combination with a Displace mod to have a animated dent moving along the waves (if you want to try this yourself, the most important thing is to set VWP distance to geometry.), making it look like something is about to break out of the water. The dent looks kinda rough around the edges though, so you think 'Aha, now is the perfect time to use the corrective smooth modifier' and add it. But then you'll see that not only does it smoothen out the dent, it also smoothens out the whole wave animation, because it only has one basis shape as a reference, which is the original flat plane. So if you have this kind of problem and want the mods to use the actual shape of each frame as the basis, this script is for you. Keep in mind that the final result will be animated completely through shapekeys though, it doesn't keep the modifiers.

#Requirements:
# - Add-on "Import-Export: NewTek MDD format"
# - Add-on "Animation: Corrective Shape Keys"
    # both of these addons can be easily enabled by going into your blender preferences and searching for them in the Add-ons Category, you don't need to download them from some third party website.
# - You need to have two versions of your object:
    # - One that shows the basic animation, in the example from above just the waves, I'll call it "main_anim". Add the modifiers you want to see applied for each frame to this object, not the other one.
    # - One that shows the complete animation, in the example the waves + the dent, from now on called "calc". (that's why I called this script retroactive, it modifies the already finished animation)

    # It's important that those two objects are animated only through shapekeys, which can be achieved by using the MDD format. I'll explain how to do that below.
    # Also they shouldn't have a different basic topology, as in e.g. number of vertices.
# - If your chosen modifiers require manual binding (as in there's a fat "bind"-button in the modifier properties panel), you need to put their names in the mods_bind_each_frame - list above, otherwise the script will not rebind them at any time.
# - Have both main_anim and calc selected (main_anim needs to be the active object), and run this script from your text editor. Now you only have to wait for it to finish.


#How to transform your animations into keyframed shapekeys using the MDD-Add-on: 
#(short note: this won't work with models that have animated changes in basic topology, like losing 3 vertices from frame 2 to 4 because of some modifier)
#1. Select your object
#2. Export it as Lightwave Point Cache (.mdd), change the export values to your needs. What will be saved in that .mdd file is the exact way your object looks like in the viewport at the time of exporting, meaning it basically acts as if all transformations, shapekeys and modifiers that are visible have been applied (including topology-altering mods like subdivision surface). If a modifier is disabled, it will be ignored by the export. In other words, make sure your object shows the animation you want the new object to have.
#3. Duplicate your object and apply all transformations as well as all visible modifiers (especially stuff like subdivision surface), delete the invisible ones. Delete all keyframes, also all shapekeys. I recommend using enabling wireframe because you need to watch out that the basic topology does not change while applying those mods. E.g. if you had a subdiv mod active while exporting, you now need to make sure that your object has that modifier applied and actually have those subdivided vertices. 
#4. With that duplicate selected, import the previously exported mdd-file. If everything went right, it should now show the exact animation as before, only that now it's animated entirely through shapekeys. If it's weirdly distorted however and doesn't animate at all it means that the topology isn't the same one as the one that was visible when you exported it, so you need to find what you forgot to apply or not apply.

#That's all you need to know.





#########################################################################
#########################Actual script begin#############################
#########################################################################
import bpy
import os


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
#########################################################################


#########################################################################
default_frame = C.scene.frame_current

#assigning the selected objects to variables
for i in C.selected_objects:
    if i == C.view_layer.objects.active:
        Original = i
    else:
        Baked = i 

select_objects([Original])
O.object.duplicate()
CopyOriginal = C.object #to prevent us seriously messing something up, we use a copy of the main_anim object instead of the original for the stuff this script does, and delete it at the end again.

#create the mdd file / the filepath.
blend_file_path = D.filepath 
directory = os.path.dirname(blend_file_path)
target_file = os.path.join(directory, 'you can delete this.mdd')



#this script depends on the objects shapekeys and their order instead of the actual keyframes to know what to do for each frame, so it "refreshes" them once by exporting/importing mdd itself.
for i in C.object.modifiers:
    i.show_viewport = False    #when exporting the mdd will save the exact way the object *looks* like in the viewport, so we need to disable all mods first
O.export_shape.mdd(filepath=target_file, frame_start=frame_start, frame_end=frame_end, fps=C.scene.render.fps, use_rest_frame=False)
O.object.shape_key_remove(all=True)
O.object.transform_apply(location=True, rotation=True, scale=True) #applying or clear doesn't matter, the transform values just have all to be default.
O.import_shape.mdd(filepath=target_file, frame_start = frame_start, frame_step=1) #first shapekey (after basis) is now keyframed to 1 at frame_start


#Instead of importing the calc animation as mdd as well, its animation will be shown with a mesh cache modifier on the same object that had the main_anim mdd imported. So one animation is shown through keyframed shapekeys, the other one through the mesh cache mod.
select_objects([Baked])
for i in C.object.modifiers:
    i.show_viewport = False
O.export_shape.mdd(filepath=target_file, frame_start=frame_start, frame_end=frame_end, fps=C.scene.render.fps, use_rest_frame=False)
select_objects([CopyOriginal])
Mesh_Cache = CopyOriginal.modifiers.new(name="Mesh Cache", type='MESH_CACHE')
Mesh_Cache.cache_format = 'MDD'
Mesh_Cache.filepath = target_file
Mesh_Cache.frame_start = frame_start
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


frame_current_overall = frame_start



#this is the stuff that happens each frame
for x in range(frame_end - frame_start + 1):
    
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
    if frame_current_overall == frame_start:
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

select_objects([CopyOriginal])
O.object.delete(use_global=False)    
#Original.hide_viewport = True
#Baked.hide_viewport = True        #disabled for now since it does hide them, but to unhide them you have to set hide_viewport to True in the console yourself again if you want to see them, since using the hide button doesn't work for some reason.
select_objects([Applied_Dupl])
Applied_Dupl.name = "beautified result"
    
    
C.scene.frame_set(default_frame)

print('Script finished')
