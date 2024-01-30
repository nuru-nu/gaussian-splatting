from pyntcloud import PyntCloud
from argparse import ArgumentParser

parser = ArgumentParser("Ply converter")
parser.add_argument("--source_path", "-s", required=True, type=str)
args = parser.parse_args()

# Read the binary PLY file
cloud = PyntCloud.from_file(args.source_path + '/point_cloud.ply')

# Write it out as an ASCII PLY file
cloud.to_file(args.source_path + '/point_cloud_ascii.ply', also_save=["mesh"], as_text=True)