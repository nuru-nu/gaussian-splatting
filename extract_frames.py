import os
import logging
import pandas as pd
from argparse import ArgumentParser

parser = ArgumentParser("ffmpeg extractor")
parser.add_argument("--source_path", "-s", required=True, type=str, help="Path to the source video")
parser.add_argument("--fps", default=2, type=float, help="Frames per second to extract")
args = parser.parse_args()

video_file = os.path.basename(args.source_path)
video_name = os.path.splitext(video_file)[0]

# Initialize the counter
counter = 1

# Create the output directory name
output_dir = "./input/" + video_name + "_in_{:04d}".format(counter)

# Check if the directory exists
while os.path.exists(output_dir):
    # If it exists, increment the counter and create a new directory name
    counter += 1
    output_dir = "./input/" + video_name + "_in_{:04d}".format(counter)

# Create the directory
os.makedirs(output_dir + "/input", exist_ok=True)

# Extract the frames
os.system("ffmpeg" + " -i " + args.source_path + " -qscale:v 1 -qmin 1 -vf fps={} ".format(args.fps) + output_dir + "/input/%04d.png")


# Create or add to the input.csv file
df = pd.DataFrame(columns=["input_folder", "video", "fps_extracted", "frame_count", "convert_time"])
input_folder = os.path.basename(output_dir)

df = df.append({"input_folder": input_folder, "video": video_file, "fps_extracted": args.fps, "frame_count": len(os.listdir(output_dir + "/input"))}, ignore_index=True)
df.to_csv("./input/input.csv", mode='a', index=False, header=not os.path.exists("./input/input.csv"))