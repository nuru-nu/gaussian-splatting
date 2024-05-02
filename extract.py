"""Extracts images in preparation for convert.py

Examples:

- `--seed 42 --sample 10` : random selection of 10 images
- `--resize 1024` : all images, resizing to 1024px (long edge)
- `--offset 1 --every 2 --num 3` : selects images 1, 3, 5 (0-based)
- `--offset 0 10 --every 3 2 --num 2 2` : selects images 0, 3, 10, 12
- `--num 10 --seed 42 --sample 2` : selects random 2 images among first 10
"""

import argparse
import glob
import os
import random
import shutil

import PIL.Image

parser = argparse.ArgumentParser('Copies / resizes (selection of) images')
parser.add_argument('--seed', default=0, help='Seed (with --sample)')
parser.add_argument('--offset', type=int, nargs='+', default=[0], help='Initial images to skip')
parser.add_argument('--every', type=int, nargs='+', default=[1], help='Every how manieth to take')
parser.add_argument('--num', type=int, nargs='+', default=[0], help='Number of images')
parser.add_argument('--sample', type=int, nargs='+', default=[0], help='Size of random sample')
parser.add_argument('--resize', type=int, help='Resize image (longer edge)')
parser.add_argument('--src', default='../../images', help='Source image directory')
parser.add_argument('--glob', default='*.jpg', help='Image glob')
parser.add_argument('--dst', default='./colmap/input', help='Destination image directory')


def zip_repeat(*args):
  n = max(map(len, args))
  def repeat(arg):
    arg = list(arg)
    return arg + [arg[-1]] * (n - len(arg))
  return zip(*map(repeat, args))


def main(args):
  src_paths = sorted(glob.glob(os.path.join(args.src, args.glob)))
  assert src_paths, f'Found no images at {args.src}/{args.glob}'
  print(f'Found {len(src_paths)} images')

  sel = set()
  random.seed(args.seed)

  for offset, every, num, sample in zip_repeat(
      args.offset, args.every, args.num, args.sample):

    paths = src_paths[offset:]
    paths = [
        path for i, path in enumerate(paths)
        if not (i % every)
    ]
    if num:
      paths = paths[:num]

    if sample:
      random.shuffle(paths)
      paths = paths[:sample]

    sel |= set(paths)

  print(f'Copying {len(sel)} images')
  
  os.makedirs(args.dst, exist_ok=True)
  for src_path in sel:
    dst_path = os.path.join(args.dst, os.path.basename(src_path))
    if args.resize:
      img = PIL.Image.open(src_path)
      img.thumbnail([args.resize, args.resize])
      img.save(dst_path)
    else:
      shutil.copy(src_path, dst_path)


if __name__ == '__main__':
  main(parser.parse_args())
