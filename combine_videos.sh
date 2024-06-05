#!/bin/bash

# Navigate to the directory containing the videos
cd /root/VideoGenerator/workspace/experiments/tutorial/ || exit

# Create the filelist.txt
rm -f filelist.txt  # Ensure filelist.txt does not already exist
for f in *.mp4; do
  echo "file '$f'" >> filelist.txt
done

# Concatenate videos
ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4

# Clean up
rm filelist.txt
