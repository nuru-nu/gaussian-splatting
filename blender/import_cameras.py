"""Imports cameras from "cameras.json" to scene."""

import json
import os

import numpy as np

import bpy


# Copied from https://github.dev/google-research/visu3d
def rot_x(angle: float, xnp=np):
  """Rotation matrix for rotation around X (in radians)."""
  c = xnp.cos(angle)
  s = xnp.sin(angle)
  R = xnp.asarray(  # pylint: disable=invalid-name
      [
          [1, 0, 0],
          [0, c, -s],
          [0, s, c],
      ]
  )
  return R


# Copied from https://github.dev/google-research/visu3d
def rot_to_euler(rot, *, eps=1e-6, xnp=np):
  """Extract euler angles from a 3x3 rotation matrix.

  Like `euler_to_rot`, it follow the z, y, x convension, BUT returns x, y, z.

  From: https://www.geometrictools.com/Documentation/EulerAngles.pdf

  Args:
    rot: Rotation matrix
    eps: Precision threshold to detect 90 degree angles.
    xnp: Np module used (jnp, tnp, np,...)

  Returns:
    The x, y, z euler angle (in radian)
  """
  r00 = rot[0, 0]
  r01 = rot[0, 1]
  r02 = rot[0, 2]
  r10 = rot[1, 0]
  r11 = rot[1, 1]
  r12 = rot[1, 2]
  r20 = rot[2, 0]
  r21 = rot[2, 1]
  r22 = rot[2, 2]

  if xnp.abs(r20) < 1.0 - eps:  # Should allow to tune the precision ?
    theta_y = xnp.arcsin(-r20)
    theta_z = xnp.arctan2(r10, r00)
    theta_x = xnp.arctan2(r21, r22)
  else:  # r20 == +1 / -1
    sign = +1 if r02 > 0 else -1

    theta_y = sign * enp.tau / 4
    theta_z = -sign * xnp.arctan2(-r12, r11)
    theta_x = 0.0

  theta_x = xnp.asarray(theta_x)
  theta_y = xnp.asarray(theta_y)
  theta_z = xnp.asarray(theta_z)
  return theta_x, theta_y, theta_z


class FileSelectOperator(bpy.types.Operator):
  """Simple Operator to use UI for loading the `cameras.json` file."""
  bl_idname = 'object.open_cameras_json'
  bl_label = 'Select a File'

  filepath: bpy.props.StringProperty(subtype="FILE_PATH")

  def execute(self, context):
    if not os.path.basename(self.filepath) == 'cameras.json':
      self.report({'ERROR'}, f'Invalid file: "{self.filepath}" - expected "cameras.json"!')
      return {'FINISHED'}

    collection = bpy.data.collections.new('cameras.json')
    bpy.context.scene.collection.children.link(collection)

    cs = json.load(open(self.filepath))
    for i, c in enumerate(cs):
      bpy.ops.object.camera_add()
      cam = bpy.context.object
      cam.name = f'Camera #{i}'
      cam.location = c['position']
      # Blender convention for Camera is to point in negative Z direction,
      # so we first want to rotate that around the X axis.
      rot = rot_to_euler(np.array(c['rotation']) @ rot_x(np.pi))
      cam.rotation_euler = rot

      collection.objects.link(cam)
      for c in bpy.data.collections:
        if c != collection and cam.name in c.objects:
          c.objects.unlink(cam)
      bpy.context.scene.collection.objects.unlink(cam)

    self.report({'INFO'}, f'Added {len(cs)} cameras from "{self.filepath}"')

    return {'FINISHED'}

  def invoke(self, context, event):
    context.window_manager.fileselect_add(self)
    return {'RUNNING_MODAL'}


def register():
  bpy.utils.register_class(FileSelectOperator)


def unregister():
  bpy.utils.unregister_class(FileSelectOperator)


if __name__ == '__main__':
  register()
  bpy.ops.object.open_cameras_json('INVOKE_DEFAULT')
