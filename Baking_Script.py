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

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import bpy

name= "__PROP_NAME__"
uri = "//__BAKING_FINAL_FOLDER__/" + name + "/"

#Get the image node that uses certain name
def checkNode(mat, name):
    nodes = mat.node_tree.nodes  
    for n in nodes:
        if(n.bl_idname == 'ShaderNodeTexImage') and ("_" + name in n.image.name):
            print(name + " image found as: " + n.image.name)
            return n  


#Get Object, MaterialSlots and create a new Image for baking
obj = bpy.context.selected_objects[0]
mats_slots = obj.material_slots
bpy.ops.image.new(name='Bake', width=2048, height=2048, color=(0.0, 0.0, 0.0, 1.0), alpha=True, generated_type='BLANK', float=False, use_stereo_3d=False, tiled=False)
img = bpy.data.images['Bake']
bake_nodes = []

#Create new img shader and assign the baking img
for m_s in mats_slots:
    mat = m_s.material
    node = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
    bake_nodes.append(node)
    node.image = img
    mat.node_tree.nodes.active = node
    
    height = checkNode(mat, 'height')
    ao = checkNode(mat, 'ao')


#Simple Bakes
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})
img.filepath_raw = uri + name + "_albedo.png"
img.file_format = 'PNG'
img.save()

bpy.ops.object.bake(type='ROUGHNESS')
img.filepath_raw = uri + name + "_roughness.png"
img.file_format = 'PNG'
img.save()

bpy.ops.object.bake(type='NORMAL')
img.filepath_raw = uri + name + "_normal.png"
img.file_format = 'PNG'
img.save()


#Delete Nodes and Images
i=0
for m_s in mats_slots:
    mat = m_s.material
    n = bake_nodes[i]
    mat.node_tree.nodes.remove(n)
    i+=1
    
bpy.data.images.remove(img)

  
    