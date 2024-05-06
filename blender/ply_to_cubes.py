"""Converts selected mesh (from PLY import) to small colored cubes."""

import bpy

# Pair programmed with ChatGPT:
# https://chat.openai.com/c/5ef0cae1-1b38-4e6b-8f18-c7b873c49f9c

# improvement ideas:
# - apply object transformation
# - choose cube size smartly


def create_material(color):
  mat = bpy.data.materials.new(name='MaterialColor')
  mat.use_nodes = True
  bsdf = mat.node_tree.nodes.get('Principled BSDF')
  bsdf.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1)
  return mat


def create_cube_at_point(location, color, parent):
  bpy.ops.mesh.primitive_cube_add(size=0.1, location=location)
  cube = bpy.context.object
  mat = create_material(color)
  if len(cube.data.materials):
    cube.data.materials[0] = mat
  else:
    cube.data.materials.append(mat)
  cube.parent = parent


def mesh_to_cubes(mesh_object):
  mesh = mesh_object.data

  bpy.ops.object.empty_add(type='PLAIN_AXES', location=mesh_object.location)
  empty_object = bpy.context.object
  empty_object.name = f'{mesh_object.name}.cubes'

  if 'Col' not in mesh.attributes:
    raise ValueError('No "Col" attribute found. Please add a "Col" attribute to the mesh.')

  col_attr = mesh.attributes['Col']
  if col_attr.domain != 'POINT' or col_attr.data_type != 'FLOAT_COLOR':
    raise ValueError('The "Col" attribute is not of type "FLOAT_COLOR" or not applied to points.')

  for i, vertex in enumerate(mesh.vertices):
    color = col_attr.data[i].color
    create_cube_at_point(vertex.co, color, empty_object)


if __name__ == '__main__':
  if not bpy.context.active_object or bpy.context.active_object.type != 'MESH':
    raise ValueError('Please select a mesh object.')
  mesh_to_cubes(bpy.context.active_object)