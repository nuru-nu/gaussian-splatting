
import argparse
import importlib.util
import json
import os

import numpy as np
import plyfile

colmap_load_spec = importlib.util.spec_from_file_location(
    'colmap_loader',
    os.path.join(os.path.dirname(__file__), 'scene/colmap_loader.py'))
colmap_loader = importlib.util.module_from_spec(colmap_load_spec)
colmap_load_spec.loader.exec_module(colmap_loader)

parser = argparse.ArgumentParser('Utility to convert files etc')
parser.add_argument(
    '--points3d_ply', action='store_true',
    help='Converts colmap/sparse/0/points3d.bin to ./points3d.ply')
parser.add_argument(
    '--cameras_json', action='store_true',
    help='Converts colmap/sparse/0/{images,cameras}.bin to cameras.json')


# Copied from ./scene/dataset_reader.py
def storePly(path, xyz, rgb):
  # Define the dtype for the structured array
  dtype = [('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
          ('nx', 'f4'), ('ny', 'f4'), ('nz', 'f4'),
          ('red', 'u1'), ('green', 'u1'), ('blue', 'u1')]
  
  normals = np.zeros_like(xyz)

  elements = np.empty(xyz.shape[0], dtype=dtype)
  attributes = np.concatenate((xyz, normals, rgb), axis=1)
  elements[:] = list(map(tuple, attributes))

  # Create the PlyData object and write to file
  vertex_element = plyfile.PlyElement.describe(elements, 'vertex')
  ply_data = plyfile.PlyData([vertex_element])
  ply_data.write(path)


# Modified from ./scene/dataset_reader.py and ./utils/camera_utils.py
def convertCameras(cam_extrinsics, cam_intrinsics):

  def qvec2rotmat(qvec):
    return np.array([
        [1 - 2 * qvec[2]**2 - 2 * qvec[3]**2,
         2 * qvec[1] * qvec[2] - 2 * qvec[0] * qvec[3],
         2 * qvec[3] * qvec[1] + 2 * qvec[0] * qvec[2]],
        [2 * qvec[1] * qvec[2] + 2 * qvec[0] * qvec[3],
         1 - 2 * qvec[1]**2 - 2 * qvec[3]**2,
         2 * qvec[2] * qvec[3] - 2 * qvec[0] * qvec[1]],
        [2 * qvec[3] * qvec[1] - 2 * qvec[0] * qvec[2],
         2 * qvec[2] * qvec[3] + 2 * qvec[0] * qvec[1],
         1 - 2 * qvec[1]**2 - 2 * qvec[2]**2]])

  cams = []
  for idx, key in enumerate(cam_extrinsics):
    extr = cam_extrinsics[key]
    intr = cam_intrinsics[extr.camera_id]
    height = intr.height
    width = intr.width

    uid = intr.id
    R = np.transpose(qvec2rotmat(extr.qvec))
    T = np.array(extr.tvec)

    if intr.model=='SIMPLE_PINHOLE':
      fy = fx = intr.params[0]
    elif intr.model=='PINHOLE':
      fx, fy = intr.params[:2]
    else:
      raise ValueError(intr.model)

    Rt = np.zeros((4, 4))
    Rt[:3, :3] = R.transpose()
    Rt[:3, 3] = T
    Rt[3, 3] = 1.0

    W2C = np.linalg.inv(Rt)
    pos = W2C[:3, 3]
    rot = W2C[:3, :3]
    serializable_array_2d = [x.tolist() for x in rot]
    cams.append({
        'id' : uid,
        'img_name' : extr.name,
        'width' : width,
        'height' : height,
        'position': pos.tolist(),
        'rotation': serializable_array_2d,
        'fy' : fy,
        'fx' : fx,
    })

  return sorted(cams, key=lambda cam: cam['img_name'])


def main(args):

  if args.points3d_ply:
    src = 'colmap/sparse/0/points3d.bin'
    base, ext = os.path.splitext(os.path.basename(src))
    dst = f'{base}.ply'
    assert os.path.exists(src)
    xyz, rgb, _ = colmap_loader.read_points3D_binary(src)
    storePly(dst, xyz, rgb)
    print(f'Converted {src} to {dst} ({len(xyz)} points)')

  if args.cameras_json:
    src = 'colmap/sparse/0/images.bin'
    cam_extrinsics = colmap_loader.read_extrinsics_binary(src)
    cam_intrinsics = colmap_loader.read_intrinsics_binary(
        src.replace('images.bin', 'cameras.bin'))
    dst = 'cameras.json'
    cams = convertCameras(cam_extrinsics, cam_intrinsics)
    with open(dst, 'w') as f:
      json.dump(cams, f)
    print(f'Stored {len(cams)} cameras in {dst}.')


if __name__ == '__main__':
  main(parser.parse_args())
