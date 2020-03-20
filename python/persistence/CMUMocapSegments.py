#TSTOP
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import time
import sys
import json
import csv
import itertools
import argparse

from Datatypes.Segments import Segments, Segment
from Datatypes.Configuration import get_filename

class CMUMocapSegments(Segments):
    """
    Segment class generated from the CMU Graphics Lab Motion Capture
    Database http://mocap.cs.cmu.edu/ 

    self.config.data_file is a dict here, where the keys are the
    classification labels. These dict structures need to be generated
    from the information on the database webpage. Unfortunately this
    is still a manual process.

    The file format is an list of records, one for each datapoint.
    Each record is an integer followed by a series of lines of the format
    label float+

    The windows and segments are generated by taking the floating
    point values of the line labels specified by config.data_index.

    e.g. if config.data_index is ['thorax', 'head'] each datapoint
    will consist of the motion capture values on the lines thorax and
    head.
    """
    def __init__(self, config) :
        super(self.__class__, self).__init__(config)
        self.config.label_index = None
        prefix = os.path.commonprefix(list(itertools.chain([[os.path.abspath(f) for f in files] for (key,files) in self.config.data_file.items()])))
        self.segments = []
        for (key,files) in self.config.data_file.items() :
            for f in files :
                p = os.path.abspath(f)[len(prefix):] 
                label = key
                with open(f,'r') as data_file :
                    data = []
                    data_element = None
                    for line in data_file :
                        try :
                            index = int(line.strip())
                            if data_element != None :
                                data.append(data_element)
                            data_element = dict([("time", index)])
                        except ValueError as e :
                            if data_element == None :
                                continue
                            else :
                                key_vals = line.strip().split(' ')
                                vals = [float(v) for v in key_vals[1:]]
                                data_element[key_vals[0]] = vals
                    if data_element != None :
                        data.append(data_element)
                data_index = []
                for i in self.config.data_index :
                    if len(data[0][i]) > 1 : 
                        for j in range(len(data[0][i])) :
                            data_index.append("%s_%d" % (i,j))
                    else :
                        data_index.append(i)
                for segment_start in range(0, len(data) - self.config.segment_size + 1, 
                                           self.config.segment_stride) :
                    segment_end = segment_start + self.config.segment_size
                    windows = [list(itertools.chain.from_iterable([itertools.chain.from_iterable([d[i] for i in self.config.data_index]) for d in data[window_start : (window_start + self.config.window_size)]]))
                               for window_start in range(segment_start, 
                                                         segment_end - self.config.window_size + 1, 
                                                         self.config.window_stride)]
                    self.segments.append(Segment(windows = windows,
                                                 segment_start = segment_start,
                                                 segment_size = self.config.segment_size,
                                                 window_stride = self.config.window_stride,
                                                 window_size = self.config.window_size,
                                                 labels = dict([(label,self.config.segment_size)]),
                                                 filename = p,
                                                 data_index = data_index,
                                                 label_index = self.config.label_index))
                print "File %s segments %s" % (p, len(self.segments))

    @staticmethod
    def get_segment_filename(config, gz=True):
        fields = ['data_file', 'data_index', 'segment_size', 'segment_stride', 'window_size', 'window_stride']
        return get_filename(config, fields, 'CMUMocapSegments', gz)

