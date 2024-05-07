"""Runs {extract,convert,train}.py on a folder structure.

The following directory structure is assumed:

root/
└── source1
    ├── runs
    │   └── run1
    │       ├── 01_extract_args.json
    │       ├── 02_convert_args.json
    │       ├── 03_helper_args.json
    │       └── models
    │           └── model1
    │               └── 01_train_args.json
    └── images
        ├── frame1.jpg
        └── frame2.jpg

Where `source1`, `exp1`, and `model1` can have sibling directories with
different configuration files. The `{command}_args.json` files refer to the
scripts `{command}.py` in the same directory as this script.

Running this script will create `{command}_results.json` and
`{command}_logs.txt` files; the latter indicates that the command finished
successfully (otherwise it would be renamed to `{command}_logs.txt_FAILED_*`).
"""

import argparse
import json
import glob
import logging
import os
import re
import shutil
import subprocess
import sys
import time

from utils import log_utils

parser = argparse.ArgumentParser('Gaussian Splatting Runner')
parser.add_argument(
    '--root_glob', default='*', help='Glob for subdirs in root folder.')
parser.add_argument(
    '--runs_glob', default='*',
    help='Glob for subdirs in runs/ folder.')
parser.add_argument(
    '--models_glob', default='*', help='Glob for subdirs in models folder.')
parser.add_argument(
    '--quiet', action='store_true', help='Drops individual tool output.')
parser.add_argument('--no_color', action='store_true')
parser.add_argument('root', help='Root directory')

arg0_path = os.path.abspath(os.path.dirname(__file__))

TQDM_RE = re.compile('.*%\\|')  # like '100%|███████| 10/10 [00:10<00:00]'


def run_command(command, basepath, quiet):
  """Executes command, returns `True` iff successful."""
  dir_path = os.path.dirname(basepath)
  py_path = os.path.join(arg0_path, f'{command}.py')
  args_path = basepath + '_args.json'
  log_path = basepath + '_logs.txt'
  results_path = basepath + '_results.json'

  if os.path.exists(log_path):
    logging.info('Skipping %s: found existing %s', command, log_path)
    return True

  logging.info('Running %s in %s', command, dir_path)
  args = json.load(open(args_path))
  cmd_args = ['python', py_path] + args
  t0 = time.time()
  ts = time.strftime('%Y%m%d_%H%M%S', time.localtime())

  with open(log_path, 'a') as f:
    logging.info('Starting %s in %s', cmd_args, dir_path)
    process = subprocess.Popen(
        cmd_args, cwd=dir_path,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    while True:
      output = process.stdout.readline()
      if output == '' and process.poll() is not None:
        break
      if TQDM_RE.match(output):
        output = output.strip('\n') + '\r'
      else:
        f.write(output)
      if not quiet:
        sys.stdout.write(output)
        sys.stdout.flush()

  dt = time.time() - t0
  returncode = process.returncode
  logging.info('Finished command after %.1f minutes', dt / 60)
  with open(results_path, 'w') as f:
    json.dump(dict(ts=ts, dt=dt, returncode=returncode, cwd=dir_path), f)

  if returncode:
    logging.fatal('Could not execute: returncode=%d', returncode)
    logging.error('Contents %s: %s', log_path, open(log_path).read())
    shutil.move(log_path, log_path + f'_FAILED_{ts}')
    return False

  return True


def glob_dir(*args):
  """Yields sorted glob of path-joined `args`, skipping "_*"."""
  for path in sorted(glob.glob(os.path.join(*args))):
    if (os.path.basename(path) + '_')[0] == '_':
      logging.info('Skipping %s', path)
      continue
    yield path


def run_directory(dir_path, quiet):
  """Calls `run_command()` on "00_{command}_args.json" files in directory."""
  for path in glob_dir(dir_path, '*_args.json'):
    basepath = path[:-len('_args.json')]
    basename = os.path.basename(basepath)
    if '_' not in basename or not basename.split('_')[0].isdigit():
      continue
    _, command = basename.split('_', 1)
    if not run_command(command, basepath, quiet):
      return False
  return True


def main(args):
  logging.info('Running with root=%s', args.root)

  for dir_path in glob_dir(args.root, args.root_glob):
    if not os.path.isdir(dir_path):
      continue

    with log_utils.log_to(os.path.join(dir_path, 'run_logs.txt')):

      video_paths = glob.glob(f'{dir_path}/*.mp4')
      video_paths = glob.glob(os.path.join(dir_path, '*.mp4'))
      image_paths = glob.glob(os.path.join(dir_path, 'images', '*.jpg'))

      if video_paths and not image_paths:
        src = video_paths[0]
        dst = os.path.join(os.path.dirname(src), 'images', 'frame_%03d.jpg')
        cmd = (
            f'mkdir -p "{os.path.dirname(dst)}" && '
            f'ffmpeg -i "{src}" -vf fps=10 "{dst}"'
        )
        logging.info(f'Expected images; you can extract frames with:\n{cmd}')
        continue

      if not image_paths:
        logging.info(f'Skipping "{dir_path}": no images')

      logging.info(f'Found {len(image_paths)} images in "{dir_path}"')

      if run_directory(dir_path, args.quiet):
        for exp_dir in glob_dir(dir_path, 'runs', args.runs_glob):
          if run_directory(exp_dir, args.quiet):
            for model_dir in glob_dir(exp_dir, 'models', args.models_glob):
              run_directory(model_dir, args.quiet)


if __name__ == '__main__':
  args = parser.parse_args()
  log_utils.setup_logging(colorize=not args.no_color)
  main(args)
