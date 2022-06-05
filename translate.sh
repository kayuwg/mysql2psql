#!/bin/bash

in_folder="origin"
out_folder="translated"

mkdir -p $out_folder

for filename in $in_folder/*; do
    go run syntax_translator.go $filename >( python3 structure_rectifier.py )  > "$out_folder/${filename##*/}"
done