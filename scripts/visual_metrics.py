#!/usr/bin/python
#
# Copyright 2010 Google Inc.
# All Rights Reserved.

"""Converts video encoding result data from text files to visualization
data source."""

__author__ = "jzern@google.com (James Zern),"
__author__ += "jimbankoski@google.com (Jim Bankoski)"

import fnmatch
import os
import string
import sys
from os.path import basename, splitext

def HasMetrics(line):
  if line[0:1] != "B":
    return True
  return False

def FileBetter(file_name_1, file_name_2, metric_column):
  """
  Compares two data files and determines which is better and by how
  much. Also produces a histogram of how much better, by PSNR.
  metric_column is the metric.
  """
  # Store and parse our two files into lists of unique tuples.

  # Read the two files, parsing out lines starting with bitrate.
  metric_set1 = set([])
  metric_file = open(file_name_1, "r")
  for line in metric_file:
    metrics = string.split(line)
    if HasMetrics(line):
      tuple = float(metrics[0]), float(metrics[metric_column])
      metric_set1.add(tuple)
  metric_set1_sorted = sorted(metric_set1)

  metric_set2 = set([])
  metric_file = open(file_name_2, "r")
  for line in metric_file:
    metrics = string.split(line)
    if line[0:1] != "B":
      tuple = float(metrics[0]), float(metrics[metric_column])
      metric_set2.add(tuple)
  metric_set2_sorted = sorted(metric_set2)

  def GraphBetter(metric_set1_sorted, metric_set2_sorted, base_is_set_2):
    """
    Search through the sorted metric file for metrics on either side of
    the metric from file 1.  Since both lists are sorted we really
    should not have to search through the entire range, but these
    are small files."""
    total_bitrate_difference_ratio = 0.0
    count = 0
    for bitrate, metric in metric_set1_sorted:
      for i in range(len(metric_set2_sorted) - 1):
        s2_bitrate_0, s2_metric_0 = metric_set2_sorted[i]
        s2_bitrate_1, s2_metric_1 = metric_set2_sorted[i + 1]
        # We have a point on either side of our metric range.
        if metric > s2_metric_0 and metric <= s2_metric_1:

          # Calculate a slope.
          if s2_metric_1 - s2_metric_0 != 0:
            metric_slope = ((s2_bitrate_1 - s2_bitrate_0) /
                            (s2_metric_1 - s2_metric_0))
          else:
            metric_slope = 0

          estimated_s2_bitrate = (s2_bitrate_0 + (metric - s2_metric_0) *
                                  metric_slope)

          # Calculate percentage difference as given by base.
          if base_is_set_2 == 0:
            bitrate_difference_ratio = ((bitrate - estimated_s2_bitrate) /
                                        bitrate)
          else:
            bitrate_difference_ratio = ((bitrate - estimated_s2_bitrate) /
                                        estimated_s2_bitrate)

          total_bitrate_difference_ratio += bitrate_difference_ratio
          count += 1
          break


    # Calculate the average improvement between graphs.
    if count != 0:
      avg = total_bitrate_difference_ratio / count

    else:
      avg = 0.0

    return avg

  # Be fair to both graphs by testing all the points in each.
  avg_improvement = (GraphBetter(metric_set1_sorted, metric_set2_sorted, 1) -
                     GraphBetter(metric_set2_sorted, metric_set1_sorted, 0)) / 2


  return avg_improvement


def HandleFiles(variables):
  """FIXME!
  """
  file_pattern = variables[1]
  baseline_dir = variables[2]
  print """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>VP8 Results</title>
<style type="text/css">
body {
  font-family: verdana;
}
.bold-font {
  font-weight: bold;
  font-size: 14px;
}

.small-font {
  font-size: 14px;
}

.header-style {
  border: 2px solid white;
  background-color: #cccccc;
}

.orange-background {
  background-color: orange;
}

.small-margin {
  margin: 0;
  padding: 0;
}

.light-gray-background {
  background-color: #f0f0f0;
}

.invisible {
  font-size: 1px;
  background-color: white;
  color: white;
  height: 0px;
}

#indented {
  position: absolute;
  left: 150px;
}

#midcol {
  margin: 0 0px;
}
</style>
<script type="text/javascript" src="http://www.google.com/jsapi"></script>
<script type="text/javascript"
  src="http://danvk.org/dygraphs/dygraph-combined.js"></script>
<script type="text/javascript">
var chart_height=600;
var chart_width=500;
var filestable =[];
var snrs =[];
"""
  # Go through each metric in the list.
  for column in range(1, 6):

    # Dirs is directories after the base to compare to the base.
    dirs = variables[3:len(variables)]

    # Find the metric files in the baseline directory.
    dir_list = sorted(fnmatch.filter(os.listdir(baseline_dir), file_pattern))

    print ("filestable[" + str(column) +
           "] =  { cols : [{id:'file',label:'File',type:'string'},")

    for directory in dirs:

      print ( "{id:'" + basename(directory) + "', label:'" +
              basename(directory) + "',type:'number'}"),
      if directory == dirs[len(dirs) - 1]:
        print "],"
      else:
        print ","

    print "rows : ["

    sumoverall = {}
    for directory in dirs:
      sumoverall[directory] = 0

    countoverall = 0
    for filename in dir_list:
      print "{c:[",
      print "{f:'" + splitext(basename(filename))[0] + "'},",
      baseline_file_name = baseline_dir + "/" + filename

      for directory in dirs:
        metric_file_name = directory + "/" + filename
        if os.path.isfile(metric_file_name):
          overall = FileBetter(baseline_file_name, metric_file_name, column)
          print "{v:" + str(100 * overall) + "}",
          if directory == dirs[len(dirs) - 1]:
            print "]",
          else:
            print ",",

          sumoverall[directory] += overall
      countoverall += 1
      print "}, "

    print "{c:[",
    print "{f:'OVERALL'},",

    for directory in dirs:
      print "{v:" + str(100 * sumoverall[directory] / countoverall) + "}",
      if directory == dirs[len(dirs) - 1]:
        print "]",
      else:
        print ",",
    print "}"
    print "]"
    print "}"
    print "snrs[" + str(column) + "] =  ["
    line_count = 0
    for filename in dir_list:
      print '"' + "{ cols : [{id:'datarate',label:'Datarate',type:'number'},",
      print ("{ id : '" + splitext(basename(filename))[0] + ":" +
             basename(baseline_dir) + "', label:'" + basename(baseline_dir) +
             "', type:'number' },"),
      for directory in dirs:
        print ("{id:'" + basename(directory) + "', label:'" +
               basename(directory) + "',type:'number'}"),
        if directory == dirs[len(dirs) - 1]:
          print "],",
        else:
          print ",",

      print "rows : [ ",

      prec = ","
      if len(dirs) > 1:
        postc = ",,,,,,,,,,,,,,,,,,,"[:len(dirs) - 1]
      else:
        postc = ""

      for directory in dirs:
        metric_file_name = directory + "/" + filename
        metric_file = open(metric_file_name, "r")
        for line in metric_file:
          metrics = string.split(line)
          if HasMetrics(line):
            print "{c:[{v:" + metrics[0] + "},",
            print prec,
            print "{v:" + metrics[column] + "}",
            print postc + "]},",
        prec += ","
        postc = postc[1:]

      baseline_file_name = baseline_dir + "/" + filename
      postc = ",,,,,,,,,,,,,,,,,,,,"[:len(dirs)]
      baseline_metric_file = open(baseline_file_name, "r")
      metric_file_lines = baseline_metric_file.readlines()
      for i in range(len(metric_file_lines)):
        line = metric_file_lines[i]
        metrics = string.split(line)
        if HasMetrics(line):
          print ("{c:[{v:" + metrics[0] + "},{v:" + metrics[column] + "}" +
                 postc + "]}"),
          if i < len(metric_file_lines) - 1:
            print ",",

      print "]" + '}"',
      line_count += 1
      if line_count < len(dir_list):
        print ","

    print "]"


  print """
var selected = 0
var imagestr = '';
var bettertable=0;
var chart=0;
var better=0;
var metricdata=0;
var metricview=0;
var column=1;
var formatter=0;
function changeColumn(col){
  column = col;
  draw_files();
}
function setup_vis(){
  chart = new google.visualization.ScatterChart(
      document.getElementById("metricgraph"));

  bettertable = new google.visualization.Table(
      document.getElementById("bettertable"));

  formatter = new google.visualization.NumberFormat(
      {fractionDigits: 1, suffix:"%"});

  draw_files();
}
function draw_files(){
  var cssClassNames = {
      'headerRow': 'blue-font small-font bold-font small-margin',
      'tableRow': 'small-font small-margin',
      'oddTableRow': 'light-gray-background small-font small-margin',
      'selectedTableRow': 'orange-background small-font',
      'hoverTableRow': 'small-font header-style',
      'headerCell': 'header-style small-margin',
      'tableCell': 'small-margin'};

  var options = {'allowHtml': true,'cssClassNames': cssClassNames};
  if (better != 0) delete better;
  better = new google.visualization.DataTable(filestable[column])
"""
  for i in range(len(dirs)):
    print "  formatter.format(better," + str(1 + i) + ");"

  print """
  bettertable.draw(better,options);
  google.visualization.events.addListener(bettertable, 'select',
                                          selectBetterHandler);
  query_file()

}
function query_file() {
  imagestr = better.getFormattedValue(selected, 0)
  var metricjson = eval('(' + snrs[column][selected] + ')');
  metricdata = new google.visualization.DataTable(metricjson, 0.6);
  if( metricview != 0 ) delete metricview;
  metricview = new google.visualization.DataView(metricdata);

  chart.draw(metricview, {curveType:'function',
      chartArea:{left:40, top:10, width:chart_width, height:chart_height - 110},
      hAxis:{title:"datarate in kbps"}, vAxis:{title:"quality in decibels"},
      legend:{position:"in"}, title:imagestr, pointSize:2, lineWidth:1,
      width:chart_width, height:chart_height - 50});

  google.visualization.events.addListener(chart, 'select', chartSelect);
  google.visualization.events.addListener(chart, 'onmouseover', chartMouseOver);
  google.visualization.events.addListener(chart, 'onmouseout', chartMouseOut);
}
function chartMouseOut(e){
  statusbar = document.getElementById('status');
  statusbar.style.display = 'none';

}
function chartMouseOver(e){
  pointDifference(e.row, e.column)
}
function pointDifference(row, col){

  if(!row || !col)
    return;

  var cols = metricdata.getNumberOfColumns();
  var rows = metricdata.getNumberOfRows();

  var sel_bitrate = metricview.getValue(row, 0 );
  var sel_metric = metricview.getValue(row, col);

  var message = "At " + sel_metric.toFixed(2) + " decibels, "
  message = message + metricdata.getColumnLabel(col) + " is <ul>"

  // col 0 is datarate
  for( var i=1;i<cols;++i){

    var metric_greatest_thats_less = 0;
    var rate_greatest_thats_less = 0;
    var metric_smallest_thats_greater = 999;
    var rate_smallest_thats_greater = 0;

    if(i==col)
      continue;

    // find the lowest metric for this column thats greater than sel_metric and
    // the highest metric for this column thats less than the metric
    for(var line_count = 0; line_count < rows; ++line_count) {
      this_metric = metricdata.getValue(line_count, i)
      this_rate = metricdata.getValue(line_count, 0)
      if(!this_metric)
        continue;

      if(this_metric > metric_greatest_thats_less &&
         this_metric < sel_metric) {
        metric_greatest_thats_less = this_metric;
        rate_greatest_thats_less = this_rate;
      }
      if(this_metric < metric_smallest_thats_greater &&
        this_metric > sel_metric) {
        metric_smallest_thats_greater = this_metric;
        rate_smallest_thats_greater = this_rate;
      }
    }

    if(rate_smallest_thats_greater == 0 || rate_greatest_thats_less == 0) {
      message = message + " <li> Couldn't find a point on both sides.</li>"
    }
    else
    {
      metric_slope = ( rate_smallest_thats_greater - rate_greatest_thats_less) /
          ( metric_smallest_thats_greater - metric_greatest_thats_less);

      projected_rate = ( sel_metric - metric_greatest_thats_less) *
          metric_slope + rate_greatest_thats_less;

      difference = 100 * (projected_rate / sel_bitrate - 1);


      if (difference > 0)
        message = message + "<li>  " + difference.toFixed(2) +
                  "% smaller than " +
                  metricdata.getColumnLabel(i) + "</li> "
      else
        message = message + "<li>  " + -difference.toFixed(2) +
                  "% bigger than " +
                  metricdata.getColumnLabel(i) + "</li> "
    }

  }
  message = message + "</ul>"
  statusbar = document.getElementById('status');
  statusbar.innerHTML = "<p>" + message + "</p>";
  statusbar.style.top = "50%";
  statusbar.style.left = "50%";
  statusbar.style.display = 'block';
}

function chartSelect(){
  var selection = chart.getSelection();
  var message = '';
  var min = metricview.getFormattedValue(selection[0].row, 0);
  var max = metricview.getFormattedValue(selection[selection.length-1].row, 0);
  var val = metricview.getFormattedValue(selection[0].row,selection[0].column);

  pointDifference(selection[0].row, selection[0].column)
  min = min / 3
  max = max * 3
  metricview.setRows(metricdata.getFilteredRows(
      [{column: 0,minValue: min, maxValue:max}]));

  chart.draw(metricview, {curveType:'function',
      chartArea:{left:40, top:10, width:chart_width, height:chart_height - 110},
      hAxis:{title:"datarate in kbps"}, vAxis:{title:"quality in decibels"},
      legend:{position:"in"}, title:imagestr, pointSize:2, lineWidth:1,
      width:chart_width, height:chart_height - 50});
}
function selectBetterHandler() {
  var selection = bettertable.getSelection();
  for (var i = 0; i < selection.length; i++) {
    item = selection[i];
  }
  selected = item.row
  query_file()
}

google.load('visualization', '1', {'packages' : ['corechart','table']});
google.setOnLoadCallback(setup_vis);
</script>
</head>

<body>

  <form name="myform"> Average size reduction to get the same quality
    <input type="radio" checked name="column" value="1"
        onClick="changeColumn('1')" />Average PSNR
    <input type="radio" name="column" value="2"
        onClick="changeColumn('2')" />Global PSNR
    <input type="radio" name="column" value="5"
        onClick="changeColumn('5')" />SSIM
  </form>

  <div id="bettertable" style="float: left"></div>
  <div id="metricgraph" style="float: left"></div>

  <div id="status"
    style='width: 300px; background-color: white; position: absolute;
    top:'50%'; left:'50%'; z-index: 1; display: none;'>
  </div>

</body>
</html>

"""
  return

if len(sys.argv) < 3:
  print """
This script creates html for displaying visually metric data produced
in a video stats file,  as created by the WEBM project when enable_psnr
is turned on:

Usage: visual_metrics.py statfile_pattern baseline_dir sub_dir [ sub_dir2 ...]

the script parses each metrics file [see below] that matches the
statfile_pattern  in the baseline directory and looks for the file that matches
that same file in each of the sub_dirs, and compares the resultant metrics
bitrate, avg psnr, glb psnr, and ssim. "

It provides a table in which each row is a file in the line directory,
and a column for each subdir, with the cells representing how that clip compares
to baseline for that subdir.   A graph is given for each which compares filesize
to that metric.  If you click on a point in the graph it zooms in on that point.

a SAMPLE metrics file:

Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
 25.911   38.242   38.104   38.258   38.121   75.790    14103
Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
 49.982   41.264   41.129   41.255   41.122   83.993    19817
Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
 74.967   42.911   42.767   42.899   42.756   87.928    17332
Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
100.012   43.983   43.838   43.881   43.738   89.695    25389
Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
149.980   45.338   45.203   45.184   45.043   91.591    25438
Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
199.852   46.225   46.123   46.113   45.999   92.679    28302
Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
249.922   46.864   46.773   46.777   46.673   93.334    27244
Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
299.998   47.366   47.281   47.317   47.220   93.844    27137
Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
349.769   47.746   47.677   47.722   47.648   94.178    32226
Bitrate  AVGPsnr  GLBPsnr  AVPsnrP  GLPsnrP  VPXSSIM    Time(us)
399.773   48.032   47.971   48.013   47.946   94.362    36203

sample use:
visual_metrics.py "*stt" vp8_20101201 vp8_teststatic vp8_teststatic2 > metrics.html
  """
else:
  HandleFiles(sys.argv)
