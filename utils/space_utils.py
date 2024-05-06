"""Utility functions for 3D transforms / renderings."""

import dataclass_array as dca
import einops
from etils.array_types import ui8
import numpy as np
import visu3d as v3d


def compute_intersection(rays: v3d.Ray['n']) -> v3d.Point3d:
  """Returns intersection point of rays."""
  A = np.zeros((3, 3))
  b = np.zeros(3)
  for ray in rays:
      A += np.outer(ray.dir, ray.dir)
      b += ray.pos * np.dot(ray.dir, ray.dir)
  center = np.linalg.solve(A, b)
  return v3d.Point3d(p=center)


def center_ray(cams: v3d.Camera) -> v3d.Ray:
  """Returns ray "at center" of cameras, looking "upwards"."""
  rays = []
  for cam in cams:
    w = cam.world_from_cam
    r = v3d.Ray(pos=w.t, dir=(w.R @ np.array([[0, 0, 1]]).T).T[0])
    rays.append(r)

  center = compute_intersection(dca.stack(rays))
  upwards = -dca.stack(rays).dir.mean(axis=0)

  return v3d.Ray(pos=center.p, dir=upwards).normalize()


def ray_to_transform(ray: v3d.Ray) -> v3d.Transform:
  """Returns transform at `ray` with Z in ray direction."""
  z_axis = ray.normalize().dir
  x_axis = np.array([1., 0, 0])
  y_axis = np.array([0, 1., 0])
  x_axis -= np.dot(x_axis, z_axis) * z_axis
  x_axis /= np.linalg.norm(x_axis)
  y_axis -= np.dot(y_axis, z_axis) * z_axis
  y_axis -= np.dot(y_axis, x_axis) * x_axis
  y_axis /= np.linalg.norm(y_axis)
  R = np.c_[x_axis, y_axis, z_axis]
  return v3d.Transform(R=R, t=ray.pos)


def camera_ball(points: v3d.Point3d['m'], cams: v3d.Camera, r=1.0) -> v3d.Point3d['n']:
  """Returns `points` that are within "camera ball" `cams`."""
  t = cams.world_from_cam.t
  c = t.mean(axis=0, keepdims=True)
  m = np.linalg.norm(t - c, axis=1).max()
  sel = np.linalg.norm(points.p - c, axis=1) < m * r
  return points[sel]


def render_tableau(points: v3d.Point3d['m'], cams: v3d.Camera['n']) -> ui8['h w 3']:
  n = int(np.ceil(len(cams) **.5))
  return einops.rearrange(
      np.r_[
          dca.stack(cams).render(points[None]),
          np.zeros([n**2 - len(cams), *cams.spec.resolution, 3], dtype='uint8'),
      ],
      '(y x) h w c -> (y h) (x w) c',
      y=n,
  )
