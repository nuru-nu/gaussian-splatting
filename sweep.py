"""Prepares directory structure for ./run.py"""

import argparse
import os
import shutil


parser = argparse.ArgumentParser('Gaussian Splatting Runner Preparer')
subparsers = parser.add_subparsers(required=True)

parser_cp = subparsers.add_parser('cp', help='Copies a directory structure')
parser_cp.add_argument('src')
parser_cp.add_argument('dst')

# parser_deflate = subparsers.add_parser('cp', help='Deflates a directory structure into a file')
# parser_deflate.add_argument('src')


def main(args: argparse.Namespace):

  if args.src and args.dst:
    src, dst = args.src.rstrip('/'), args.dst.rstrip('/')
    paths, existed = [], []
    for dirpath, dirnames, filenames in os.walk(src):
      for filename in filenames:
        if not filename.endswith('_args.json'):
          continue
        num_command = filename[:-len('_args.json')]
        if not num_command.split('_')[0].isdigit():
          continue
        dstdirpath = dst + dirpath[len(src):]
        os.makedirs(dstdirpath, exist_ok=True)
        paths.append(os.path.join(dstdirpath, filename))
        if os.path.exists(paths[-1]):
          existed.append(paths[-1])
        else:
          shutil.copy(os.path.join(dirpath, filename), paths[-1])
    print(f'Copied {src}/ to {dst}/: {len(paths)} files, {len(existed)} existed already.')


if __name__ == '__main__':
  main(parser.parse_args())
