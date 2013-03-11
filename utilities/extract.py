import csv
import logging
import optparse
import os
import re
import sys
import tempfile
import yaml

NO_ORIGINAL=True

def getcsv(name, instance, data, outfilename, log):
  csvfile = open(outfilename, 'w')
  datawriter = csv.writer(csvfile, delimiter=',')
#  datawriter.writerow(['datasize', 'original', 'pbesparelm', 'pbesstategraph'])
  header = []
  rows = []
  
  for (case, instances) in data.items():
    if case.startswith('{0} '.format(name)):
      parameters = case[case.find('[')+1: case.find(']')]
      parameters = parameters.split(',')
      if header == []:
        for p in parameters:
          p = p.split('=')
          header.append(p[0].strip())
      args = []
      for p in parameters:
        p = p.split('=')
        args.append(p[1].strip())

      rows.append(args + [instances[instance].setdefault('original',{}).setdefault('sizes', {}).setdefault('eqns', 'NaN'), instances[instance]['pbesparelm']['sizes']['eqns'], instances[instance]['pbesstategraph']['sizes']['eqns']])
       
  datawriter.writerow(header + ['original', 'pbesparelm', 'pbesstategraph']) 

  for row in sorted(rows, cmp=lambda x,y: cmp(int(x[0]), int(y[0]))):
    datawriter.writerow(row)
  csvfile.close()
  return csvfile.name

def run(infilename, outfilename, name, instance, log):
  data = yaml.load(open(infilename).read())
  getcsv(name, instance, data, outfilename, log)
  
def runCmdLine():
  parser = optparse.OptionParser(usage='usage: %prog [options] infile outfile')
  parser.add_option('-v', action='count', dest='verbosity',
                    help='Be more verbose. Use more than once to increase verbosity even more.')
  parser.add_option('-n', '--name', dest='name',
                    help='Generate plot for problem NAME', metavar='NAME',
                    default='Lossy buffer')
  parser.add_option('-i', '--instance', dest='instance',
                    help='Generate plot for problem INSTANCE', metavar='INSTANCE',
                    default='received_no_other_read_then_delivered')
  options, args = parser.parse_args()
  if len(args) < 2:
    parser.error(parser.usage)
  
  infilename = args[0]
  outfilename = args[1]

  logging.basicConfig()
  if options.verbosity > 0:
    logging.getLogger('extract').setLevel(logging.INFO)
  
  run(infilename, outfilename, options.name, options.instance, logging.getLogger('extract'))

if __name__ == '__main__':
  runCmdLine()
