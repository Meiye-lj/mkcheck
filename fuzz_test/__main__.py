#!/usr/bin/env python

import os
import subprocess
import stat
import sys
import time

from graph import parse_graph
from parser import find_outputs
from proc import run_proc

# Project directory.
scriptPath = os.path.dirname(os.path.abspath(__file__))
projectPath = os.path.abspath(os.path.join(scriptPath, os.pardir))
toolPath = os.path.join(projectPath, 'build/mkcheck')
rootPath = os.getcwd()

# TODO: make this an actual temporary folder
tmpPath = os.path.join(projectPath, 'tmp')

# Build mkcheck.
run_proc([ "ninja" ], cwd=os.path.join(projectPath, 'build'))

# Run a clean build.
run_proc([ "make", "clean" ], cwd=rootPath)

# Find the initial timestamps of the tracked files.
tracked = set()
for dirName, subdirList, fileList in os.walk(rootPath, topdown=False):
  for fileName in fileList:
    tracked.add(os.path.join(dirName, fileName))

timestamps = {}
for entry in tracked:
  timestamps[entry] = os.stat(entry).st_mtime

# Run the build with mkcheck.
graphPath = os.path.join(tmpPath, 'out_clean')
run_proc(
  [
    toolPath,
    "--output={0}".format(graphPath),
    "make"
  ],
  cwd=rootPath
)

graph = parse_graph(rootPath, graphPath)

# Run the build after touching each file.
for idx, file in zip(range(len(tracked)), tracked):
    print file
    # Touch the file.
    os.utime(file, None)

    # Run the incremental build.
    metaDir = os.path.join(tmpPath, 'out_{0}'.format(idx))
    run_proc(
    [
      toolPath,
      "--output={0}".format(metaDir),
      "make"
    ],
    cwd=rootPath
    )

    deps = graph.find_deps(file[len(rootPath) + 1:])
    outs = find_outputs(rootPath, metaDir)
    if deps != outs:
        print '%s:' % file
        for dep in deps:
            if dep not in outs:
                print '\t-', dep
        for out in outs:
            if out not in deps:
                print '\t+', out

    with open(os.path.join(metaDir, 'file'), 'w') as out:
        out.write(file)
