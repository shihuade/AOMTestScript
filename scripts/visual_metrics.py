#!/usr/bin/python2.4
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


def FileBetter(fn1, fn2, p):
  """
  Compares two data files and determines which is better and by how
  much. Also produces a histogram of how much better, by PSNR.
  p is the metric.
  """
  # Store and parse our two files into lists of unique tuples
  up = set([])

  # Read the two files, parsing out lines starting with bitrate
  f = open(fn1, "r")
  for line in f:
    f = string.split(line)
    if line[0:1] != "B":
      x = float(f[0]), float(f[p])
      up.add(x)
  u = sorted(up)
  vp = set([])

  f = open(fn2, "r")
  for line in f:
    f = string.split(line)
    if line[0:1] != "B":
      x = float(f[0]), float(f[p])
      vp.add(x)
  v = sorted(vp)

  def GraphBetter(u, v, t):
    """
    Search through the sorted PSNR file for PSNRs on either side of
    the PSNR from file 1.  Since both lists are sorted we really
    should not have to search through the entire range, but these
    are small files.."""
    total = 0.0
    c = 0
    for br, psnr in u:
      for i in range(len(v) - 1):
        b0, p0 = v[i]
        b1, p1 = v[i+1]
        # We have a point on either side of our PSNR range
        if psnr > p0 and psnr <= p1:

          # Calculate a slope
          if p1-p0 != 0:
            s = (b1-b0)/(p1-p0)
          else:
            s = 0

          ebr = b0 + (psnr-p0) * s
          # Calculate percentage difference in which direction?
          if t == 0:
            d = (br - ebr) / br
          else:
            d = (br - ebr) / ebr

          total += d
          c += 1
          break

    # Calculate the average improvement between graphs
    if c != 0:
      avg = total/c
    else:
      avg = 0.0
    return avg

  # Be fair to both graphs
  a = GraphBetter(u, v, 1)
  b = GraphBetter(v, u, 0)
  c = (a-b)/2

  return c


def HandleFiles(variables):
  """FIXME!
  """
  base = variables[1]
  old = variables[2]
  print """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
   "http://www.w3.org/TR/html4/loose.dtd">
<html lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<title>VP8 Results</title>
<style type="text/css">
.bold-font { font-weight: bold; font-size: 14px;}
.small-font { font-size: 14px;}
.gold-border { border: 2px solid white;  background-color: #eeeeff;}
.orange-background {  background-color: orange; }
.small-margin { margin: 0; padding: 0;}
.beige-background { background-color: beige; }
.invisible { font-size: 1px; background-color:white;color:white; height: 0px;}
#indented{position:absolute;left :150px;}
#midcol{margin:0 0px;}
</style>
<script type="text/javascript" src="http://www.google.com/jsapi"></script>
<script type="text/javascript" src="http://danvk.org/dygraphs/dygraph-combined.js"></script>
<script type="text/javascript">
"""

  print "var filestable =[];"
  print "var snrs =[];"

  for column in range(1, 6):
    dirs = variables[3:len(variables)]

    dir_list = sorted(fnmatch.filter(os.listdir(base+"/"+old), "*.stt"))

    print "filestable[" + str(column) + "] =  { cols : [{id:'file',label:'File',type:'string'},"

    for d in dirs:
      print "{id:'" +d+"', label:'"+d+"',type:'number'}",
      if d == dirs[len(dirs)-1]:
        print "],"
      else:
        print ","

    print "rows : ["

    sumoverall = {}
    for d in dirs:
      sumoverall[d] = 0

    countoverall = 0
    for f in dir_list:
      print "{c:[",
      print "{f:'"+f+"'},",
      o = base +"/" + old + "/" + f

      for d in dirs:
        n = base +"/" + d + "/" + f
        if os.path.isfile(n):
          overall = FileBetter(o, n, column)
          print "{v:" +str(100*overall) +"}",
          if d == dirs[len(dirs)-1]:
            print "]",
          else:
            print ",",

          sumoverall[d] += overall
      countoverall+=1
      print "}, "

    print "{c:[",
    print "{f:'OVERALL'},",
    for d in dirs:
      print "{v:" +str(100*sumoverall[d]/countoverall) +"}",
      if d == dirs[len(dirs)-1]:
        print "]",
      else:
        print ",",
    print "}"
    print "]"
    print "}"

    print "snrs[" + str(column) + "] =  ["
    j = 0
    for f in dir_list:
      print '"' +"{ cols : [{id:'datarate',label:'Datarate',type:'number'},",
      print "{ id : '" + f +":" + old + "', label:'" + old + "', type:'number' },",
      for d in dirs:
        print "{id:'" +d+"', label:'"+d+"',type:'number'}",
        if d == dirs[len(dirs)-1]:
          print "],",
        else:
          print ",",

      print "rows : [ ",

      prec = ","
      if len(dirs) > 1:
        postc = ",,,,,,,,,,,,,,,,,,,"[:len(dirs)-1]
      else:
        postc = ""
      for d in dirs:
        n = base +"/" + d + "/" + f
        a = open(n, "r")
        for line in a:
          g = string.split(line)
          if g[0] != "Bitrate":
            print "{c:[{v:"+g[0] +"},",
            print prec,
            print "{v:"+g[column]+"}",
            print postc + "]},",
        prec += ","
        postc = postc[1:]

      o = base +"/" + old + "/" + f
      postc = ",,,,,,,,,,,,,,,,,,,,"[:len(dirs)]
      f = open(o, "r")
      l = f.readlines()
      for i in range(len(l)):
        line = l[i]
        f = string.split(line)
        if f[0] != "Bitrate":
          print "{c:[{v:"+f[0] +"},{v:"+f[column]+"}"+postc+"]}",
          if i < len(l)-1:
            print ",",

      print "]"+'}"',
      j += 1
      if j < len(dir_list):
        print ","

    print "]"

  print """
var selected = 0
var imagestr = '';
var bettertable=0;
var chart=0;
var better=0;
var psnrdata=0;
var psnrview=0;
var column=1;
var formatter=0;
function changeColumn(col){
  column = col;
  draw_files();
}
function setup_vis(){
  chart = new google.visualization.ScatterChart(document.getElementById("psnrgraph"));
  bettertable = new google.visualization.Table(document.getElementById("bettertable"));
  formatter = new google.visualization.NumberFormat({fractionDigits: 2});
  draw_files();
}
function draw_files(){
  var cssClassNames = {
      'headerRow': 'blue-font small-font bold-font small-margin',
      'tableRow': 'small-font small-margin',
      'oddTableRow': 'beige-background small-font small-margin',
      'selectedTableRow': 'orange-background small-font',
      'hoverTableRow': 'small-font gold-border',
      'headerCell': 'gold-border small-margin',
      'tableCell': 'small-margin'};

  var options = {height:640, 'allowHtml': true,'cssClassNames': cssClassNames};
  if (better !=0) delete better;
  better = new google.visualization.DataTable(filestable[column])
"""
  for i in range(len(dirs)):
    print "  formatter.format(better," + str(1+i) +");"

  print """
  bettertable.draw(better,options);
  google.visualization.events.addListener(bettertable, 'select', selectBetterHandler);
  query_file()

}
function query_file() {
  imagestr = better.getFormattedValue(selected,0)
  var psnrjson = eval('(' + snrs[column][selected] + ')');
  psnrdata = new google.visualization.DataTable(psnrjson, 0.6);//new google.visualization.DataTable((psnr)s, 0.6);
  if( psnrview != 0 ) delete psnrview;
  psnrview = new google.visualization.DataView(psnrdata);
  chart.draw(psnrview, {curveType:'function',title:imagestr,pointSize:2,lineWidth:1,width:840,height:640  });
  google.visualization.events.addListener(chart, 'select', chartSelect);
}
function chartSelect(){
  var selection = chart.getSelection();
  var message = '';
  var min = psnrview.getFormattedValue(selection[0].row,0);
  var max = psnrview.getFormattedValue(selection[selection.length-1].row,0);
  min = min / 3
  max = max * 3
  psnrview.setRows(psnrdata.getFilteredRows([{column: 0,minValue: min, maxValue:max}]));
  chart.draw(psnrview, {curveType:'function',title:imagestr,pointSize:2,lineWidth:1,width:840,height:640  });
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

<body >
  <form name="myform">
    <input type="radio" checked name="column" value="1" onClick="changeColumn('1')" />Avg PSNR
    <input type="radio" name="column" value="2" onClick="changeColumn('2')" />Glb PSNR
    <input type="radio" name="column" value="1" onClick="changeColumn('3')" />PP Avg PSNR
    <input type="radio" name="column" value="2" onClick="changeColumn('4')" />PP Glb PSNR
    <input type="radio" name="column" value="5" onClick="changeColumn('5')" />SSIM
  </form>
  <div id="bettertable" style="float:left"></div>
  <div id="psnrgraph" style="float:left"></div>
</body>
</html>
"""
  return

if len(sys.argv) < 3:
  print """
This script creates html for displaying visually metric data produced
in a video stats file,  as created by the WEBM project when enable_psnr
is turned on:

Usage: visual_metrics.py base_directory baseline_dir sub_dir [ sub_dir2 ...]

the script parses each metrics file [see below] in the baseline directory =>
base_directory/baseline_dir and looks for that same file in each of the
sub_dirs, and compares the resultant metrics bitrate, avg psnr, glb psnr,
pp avg psnr, pp glb psnr, and ssim. "
It provides a table in which each row is a file in the baseline directory,
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
visual_metrics.py . vp8_20101201 vp8_teststatic vp8_teststatic2 > metrics.html
  """
else:
  HandleFiles(sys.argv)
