import logging
import optparse
import sys
import yaml

def run(infilename, outfilename, log):
  data = yaml.load(open(infilename).read())
  newdata = {}
  
  for (case, instances) in data.items():
    for (instance, tools) in instances.items():
      if tools['original']['solution'] != tools['pbesparelm']['solution'] and tools['original']['solution'] != 'unknown' and tools['pbesparelm']['solution'] != 'unknown':
        print 'The solution of the original PBES and parelm reduced PBES differ for {0} -- {1}'.format(case, instance)
        print '  solution of the original:           {0}'.format(tools['original']['solution'])
        print '  solution of the parelm reduced:     {0}'.format(tools['pbesparelm']['solution'])
      if tools['original']['solution'] != tools['pbesstategraph']['solution'] and tools['original']['solution'] != 'unknown' and tools['pbesstategraph']['solution'] != 'unknown':
        print 'The solution of the original PBES and stategraph reduced PBES differ for {0} -- {1}'.format(case, instance)
        print '  solution of the original:           {0}'.format(tools['original']['solution'])
        print '  solution of the stategraph reduced: {0}'.format(tools['pbesstategraph']['solution'])
      if tools['pbesparelm']['solution'] != tools['pbesstategraph']['solution'] and tools['pbesparelm']['solution'] != 'unknown' and tools['pbesstategraph']['solution'] != 'unknown':
        print 'The solution of the parelm reduced PBES and stategraph reduced PBES differ for {0} -- {1}'.format(case, instance)
        print '  solution of the parelm reduced:     {0}'.format(tools['pbesparelm']['solution'])
        print '  solution of the stategraph reduced: {0}'.format(tools['pbesstategraph']['solution'])

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
