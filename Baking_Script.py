"""
MIT License

Copyright (c) 2022 Mauricio Meza Burbano

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OFa ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import bpy

#<-------------------------------------------------------->
#----->THIS ARE THE INITIAL PARAMETERS OF THE SCRIPT<------
#--the name of your asset/prop
name= "_PROP_NAME"
#--if you want maps to be saved in the same folder just leave it as "//"
uri = "//"
#--if you dont want Metallness or AO change this to False
metal = True
ao = True
#--if you want to create a new object with all baked textures turn this to true
duplicate = True
#<-------------------------------------------------------->

bpy.context.scene.render.engine = 'CYCLES'


#-----INITIAL SETTINGS----
#--Get Object, MaterialSlots and create a new Image for baking
obj = bpy.context.selected_objects[0]
mats_slots = obj.material_slots


bpy.ops.image.new(name='Bake', width=512, height=512, color=(0.0, 0.0, 0.0, 1.0), alpha=True, generated_type='BLANK', float=False, use_stereo_3d=False, tiled=False)
img = bpy.data.images['Bake']
bake_nodes = []

#--Create new img shader and assign the baking img
for m_s in mats_slots:
    mat = m_s.material
    node = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
    bake_nodes.append(node)
    node.image = img
    mat.node_tree.nodes.active = node


#-----ALBEDO BAKING WITOUTH METALLNESS----
#--Disconnect metals if there are any
if(metal):
    metal_texs = []
    metal_vals = []
    for m_s in mats_slots:
        mat = m_s.material
        nodes = mat.node_tree.nodes  
        for n in nodes:
            #Find Principled BSDF and change metallic inputs
            if(n.bl_idname == 'ShaderNodeBsdfPrincipled'):
                    metal_socket = n.inputs[4]
                    if(metal_socket.default_value > 0):
                        metal_vals.append([metal_socket, metal_socket.default_value])
                        metal_socket.default_value = 0
                    if(metal_socket.is_linked):
                        metal_out_socket = metal_socket.links[0].from_socket 
                        mat.node_tree.links.remove(metal_socket.links[0])
                        metal_texs.append([mat, metal_socket, metal_out_socket])                     

#--Albedo Bake
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})
img.filepath_raw = uri + name + "_albedo.png"
img.file_format = 'PNG'
img.save()

#--Reconnect metals if there were any
if(metal):
    for m_n in metal_texs:
        m_n[0].node_tree.links.new(m_n[1], m_n[2])
    for m_n in metal_vals:
        m_n[0].default_value = m_n[1]
   

#-----ROUGHNESS, NORMAL AND AO BAKING----     
#--Simple Bakes
bpy.ops.object.bake(type='ROUGHNESS')
img.filepath_raw = uri + name + "_roughness.png"
img.file_format = 'PNG'
img.save()

bpy.ops.object.bake(type='NORMAL')
img.filepath_raw = uri + name + "_normal.png"
img.file_format = 'PNG'
img.save()

if(ao):
    bpy.ops.object.bake(type='AO')
    img.filepath_raw = uri + name + "_ao.png"
    img.file_format = 'PNG'
    img.save()


#-----METALNESS BAKING---- 
#--Settings for Metal Baking
if(metal):
    metal_tex_nodes = []
    metal_col_nodes = []
    metal_mix_nodes = []
    
    for m_s in mats_slots:
        mat = m_s.material
        nodes = mat.node_tree.nodes  
        for n in nodes:
            #Find Principled BSDF and change metallic and roughness inputs
            if(n.bl_idname == 'ShaderNodeBsdfPrincipled'):
                    metal_socket = n.inputs[4]
                    rough_socket = n.inputs[7]
                    #Change image-tex for nodes that need it
                    if(metal_socket.is_linked) and (rough_socket.is_linked):
                        metal_out_socket = metal_socket.links[0].from_socket
                        rough_out_socket = rough_socket.links[0].from_socket
                        mat.node_tree.links.new(metal_socket, rough_out_socket)
                        mat.node_tree.links.new(metal_out_socket, rough_socket)
                        metal_tex_nodes.append([mat, metal_socket, metal_out_socket, rough_socket, rough_out_socket])
                    #Change only color value for nodes that need it
                    elif(not metal_socket.is_linked) and (not rough_socket.is_linked):
                        aux = metal_socket.default_value
                        metal_socket.default_value = rough_socket.default_value
                        rough_socket.default_value = aux
                        metal_col_nodes.append([metal_socket, rough_socket, metal_socket])
                    #Change mix color value adn tex for nodes that need it
                    elif(not metal_socket.is_linked) and (rough_socket.is_linked):
                        aux = metal_socket.default_value
                        rough_out_socket = rough_socket.links[0].from_socket
                        node_link = mat.node_tree.links.new(metal_socket, rough_out_socket)
                        mat.node_tree.links.remove(rough_socket.links[0])
                        rough_socket.default_value = aux
                        metal_mix_nodes.append([mat, node_link, rough_socket, rough_out_socket])
                   
    #-Simple Metallnes Bake with metallic values
    bpy.ops.object.bake(type='ROUGHNESS')
    img.filepath_raw = uri + name + "_metallic.png"
    img.file_format = 'PNG'
    img.save()
    
    #-Return all sockets materials to old textures and colors
    for m_n in metal_tex_nodes:
        m_n[0].node_tree.links.new(m_n[1], m_n[2])
        m_n[0].node_tree.links.new(m_n[3], m_n[4])

    for m_n in metal_col_nodes:
        aux = m_n[1].default_value
        m_n[1].default_value = m_n[2].default_value
        m_n[2].default_value = aux 
        
    for m_n in metal_mix_nodes:
        m_n[0].node_tree.links.remove(m_n[1])
        m_n[0].node_tree.links.new(m_n[2], m_n[3])


#-----FINAL SETTINGS---- 
#--Delete Nodes and Images
i=0
for m_s in mats_slots:
    mat = m_s.material
    n = bake_nodes[i]
    mat.node_tree.nodes.remove(n)
    i+=1
bpy.data.images.remove(img) 


#-----DUPLICATE THE OBJECT WITH THE BAKED TEXTURES----
if(duplicate):
    #-create new object, rename it and move it
    dup_obj = obj.copy()
    dup_obj.data = obj.data.copy()
    bpy.context.collection.objects.link(dup_obj)
    obj.name = name+" PBR"
    dup_obj.name = name
    
    #-remove all materials
    dup_mat_slots = dup_obj.material_slots
    for mat_slot in dup_mat_slots:
        dup_obj.active_material_index = 0
        bpy.ops.object.material_slot_remove()
     
    #-create new material
    pbr_mat = bpy.data.materials.new(name=name+" PBR")
    pbr_mat.use_nodes = True  
    
    
    #-load images
    alb_node = pbr_mat.node_tree.nodes.new(type='ShaderNodeTexImage')
    bpy.ops.image.open(filepath=uri+name+"_albedo.png")
    bpy.data.images[name+"_albedo.png"].pack()
    alb_node.image = bpy.data.images[name+"_albedo.png"]
    alb_node_out = alb_node.outputs[0]
    
    rgh_node = pbr_mat.node_tree.nodes.new(type='ShaderNodeTexImage')
    bpy.ops.image.open(filepath=uri+name+"_roughness.png")
    bpy.data.images[name+"_roughness.png"].pack()
    rgh_node.image = bpy.data.images[name+"_roughness.png"]
    rgh_node_out = rgh_node.outputs[0]
    
    if(metal):
        mtl_node = pbr_mat.node_tree.nodes.new(type='ShaderNodeTexImage')    
        bpy.ops.image.open(filepath=uri+name+"_metallic.png")
        bpy.data.images[name+"_metallic.png"].pack()
        mtl_node.image = bpy.data.images[name+"_metallic.png"]
        mtl_node_out = mtl_node.outputs[0]
        
        
    #find Principled BSDF and link images to bsdf
    nodes = pbr_mat.node_tree.nodes  
    for n in nodes:
        if(n.bl_idname == 'ShaderNodeBsdfPrincipled'):
            albdo_socket = n.inputs[0]
            pbr_mat.node_tree.links.new(alb_node_out, albdo_socket)
            rough_socket = n.inputs[7]
            pbr_mat.node_tree.links.new(rgh_node_out, rough_socket)
            if(metal):
                metal_socket = n.inputs[4]
                pbr_mat.node_tree.links.new(mtl_node_out, metal_socket)   
                
    obj.data.materials.append(pbr_mat)
    obj.location[0] = 1
    
"""
BUGS AND TODO:
- Check for Empty Material_Slots
- MetalTex + RoughnessVal in Metal Baking Process
- Normal in Duplication
"""