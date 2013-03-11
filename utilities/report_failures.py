import logging
import optparse
import sys
import yaml

def run(infilename, outfilename, log):
  data = yaml.load(open(infilename).read())
  newdata = {}
  failures = []

  for (case, instances) in data.items():
    for (instance, tools) in instances.items():
      if tools['original'] == 'failed':
        failures.append((case, instance))

  for (case,instance) in sorted(failures):
    print 'Generation of {0} -- {1} failed'.format(case, instance)

def runCmdLine():
  parser = optparse.OptionParser(usage='usage: %prog [options] infile')
  parser.add_option('-v', action='count', dest='verbosity',
                    help='Be more verbose. Use more than once to increase verbosity even more.')
  options, args = parser.parse_args()
  if len(args) < 1:
    parser.error(parser.usage)
  
  infilename = args[0]
  outfilename = None  
  if len(args) >= 2:
    outfilename = args[1]

  logging.basicConfig()
  if options.verbosity > 0:
    logging.getLogger('pruning').setLevel(logging.INFO)
  
  run(infilename, outfilename, logging.getLogger('pruning'))

if __name__ == '__main__':
  runCmdLine()
