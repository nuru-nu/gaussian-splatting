
import argparse
import importlib.util
import os

import numpy as np
import plyfile

colmap_load_spec = importlib.util.spec_from_file_location(
    'colmap_loader',
    os.path.join(os.path.dirname(__file__), 'scene/colmap_loader.py'))
colmap_loader = importlib.util.module_from_spec(colmap_load_spec)
colmap_load_spec.loader.exec_module(colmap_loader)

parser = argparse.ArgumentParser('Utility to convert files etc')
subparsers = parser.add_subparsers(title='command', required=True)
convert_ply_parser = subparsers.add_parser('convert_ply')
convert_ply_parser.add_argument('points3d_bin')


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


def main(args):
  if args.points3d_bin:
    src = args.points3d_bin
    base, ext = os.path.splitext(src)
    dst = f'{base}.ply'
    assert os.path.exists(src)
    xyz, rgb, _ = colmap_loader.read_points3D_binary(src)
    storePly(dst, xyz, rgb)
    print(f'Converted {src} to {dst} ({len(xyz)} points)')


if __name__ == '__main__':
  main(parser.parse_args())
