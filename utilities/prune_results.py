import logging
import optparse
import sys
import yaml

def run(infilename, outfilename, log):
  data = yaml.load(open(infilename).read())
  newdata = {}
  
  for (case, instances) in data.items():
    for (instance, tools) in instances.items():
      if tools['pbesstategraph']['sizes'] != tools['pbesparelm']['sizes']:
        newdata.setdefault(case,{})[instance] = tools
        #print tools
        log.info('Keeping {0} - {1}'.format(case, instance))
      else:
        log.info('Removing {0} - {1} because there is no additional reduction with stategraph compared to parelm'.format(case, instance))
  
  
  if outfilename:
    outfile = open(outfilename, 'w')
  else:
    outfile = sys.stdout
    
  outfile.write(yaml.dump(newdata))
  outfile.close()

def runCmdLine():
  parser = optparse.OptionParser(usage='usage: %prog [options] infile [outfile]')
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