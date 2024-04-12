import os
import logging
import pandas as pd
from argparse import ArgumentParser

parser = ArgumentParser("automation")
parser.add_argument("--source_path", "-s", required=True, type=str, help="Path to the source video")
parser.add_argument("--fps", default=2, type=float, help="Frames per second to extract")
parser.add_argument("--resolution", "-r", default="2", type=float, help="Training resolution 1/x of the frames")
parser.add_argument("--iterations", "-it", default="7_000", type=int, help="Number of iterations to train")
parser.add_argument("--test_steps", "-ts", default="1000", type=int, help="Test every n steps")
args = parser.parse_args()

# extract frames
os.system("extraxt_frames.py -s " + args.source_path + " --fps " + args.fps)
from extract_frames import input_folder

# convert frames
os.system("convert.py -s ./input/" + input_folder)

# train model
os.system("train.py -s ./input/" + input_folder + " -r " + args.resolution + " -it " + args.iterations + " -ts " + args.test_steps + " --eval")
from train import model_path

# render model
os.system("render.py -m ./output/" + model_path)