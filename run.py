"""Runs {extract,convert,train}.py on a folder structure.

The following directory structure is assumed:

root/
└── source1
    ├── experiments
    │   └── exp1
    │       ├── extract_args.json
    │       ├── convert_args.json
    │       ├── helper_args.json
    │       └── models
    │           └── model1
    │               └── train_args.json
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
import shutil
import subprocess
import sys
import time

from utils import log_utils

parser = argparse.ArgumentParser('Gaussian Splatting Runner')
parser.add_argument(
    '--root_glob', default='*', help='Glob for subdirs in root folder.')
parser.add_argument(
    '--experiments_glob', default='*',
    help='Glob for subdirs in experiments folder.')
parser.add_argument(
    '--models_glob', default='*', help='Glob for subdirs in models folder.')
parser.add_argument('root', help='Root directory')

arg0_path = os.path.abspath(os.path.dirname(__file__))


def run_command(command, dir_path):
  py_path = os.path.join(arg0_path, f'{command}.py')
  args_path = os.path.join(dir_path, f'{command}_args.json')
  log_path = os.path.join(dir_path, f'{command}_logs.txt')
  results_path = os.path.join(dir_path, f'{command}_results.json')

  if os.path.exists(log_path):
    logging.info('Skipping %s: found existing %s', command, log_path)
    return
  if not os.path.exists(args_path):
    logging.warning('Skipping %s: missing %s', command, args_path)
    return

  logging.info('Running %s in %s', command, dir_path)
  args = json.load(open(args_path))
  cmd_args = ['python', py_path] + args
  t0 = time.time()
  ts = time.strftime('%Y%m%d_%H%M%S', time.localtime())

  with open(log_path, 'a') as f:
    logging.info('Starting %s', cmd_args)
    result = subprocess.run(
        cmd_args, stdout=f, stderr=subprocess.STDOUT, cwd=dir_path)

  dt = time.time() - t0
  logging.info('Finished command after %.1f minutes', dt / 60)
  with open(results_path, 'w') as f:
    json.dump(dict(ts=ts, dt=dt, returncode=result.returncode, cwd=dir_path), f)

  if result.returncode:
    # import pdb; pdb.set_trace()
    logging.fatal('Could not execute: %s', result)
    logging.error('Contents %s: %s', log_path, open(log_path).read())
    shutil.move(log_path, log_path + f'_FAILED_{ts}')
    sys.exit(1)


def glob_dir(*args):
  for path in sorted(glob.glob(os.path.join(*args))):
    if os.path.basename(path)[0] == '_':
      logging.info('Skipping %s', path)
      continue
    yield path


def process(subdir_path, models_glob):
  run_command('extract', subdir_path)
  run_command('convert', subdir_path)
  run_command('helper', subdir_path)
  for model_path in glob_dir(subdir_path, 'models', models_glob):
    run_command('train', model_path)


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

      for subdir_path in glob_dir(dir_path, 'experiments', args.experiments_glob):
        if os.path.isdir(subdir_path):
          process(subdir_path, args.models_glob)


if __name__ == '__main__':
  log_utils.setup_logging()
  main(parser.parse_args())
