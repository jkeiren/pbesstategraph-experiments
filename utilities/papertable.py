import csv
import logging
import optparse
import os
import re
import sys
import tempfile
import yaml
import datetime

def addsep(number):
  if number == '??':
    return number
    
  result = '{:,}'.format(int(number))
  return result

def getrowsizes(data, case, property):
  casedata = data[case][property]
  sizes = {}
  solutions = {}
  
  for tool in ['original', 'pbesparelm', 'pbesstategraph (global)', 'pbesstategraph (local)']:
    size = casedata.get(tool, {}).get('sizes', {})
    if size == 'unknown':
      size = {}
    sizes[tool] = addsep(size.get('eqns', '??'))
    
    solutions[tool] = casedata.get(tool, {}).get('solution', 'unknown')
    
  solution = '??'
  for v in solutions.values():
    if v != 'unknown':
      if v not in ['true', 'false']:
        print "Unexpected solution for {0}, {1}"
        continue
        
      if solution != '??' and v != solution:
        print "Different solutions for {0}, {1}".format(case, property)
      solution = v

  if solution == 'true':
    solstr = '\\surd'
  elif solution == 'false':
    solstr = '\\times'
  else:
    solstr = solution
    
  return ' && {0} && {1} && {2} && {3} && ${4}$ \\\\'.format(sizes['original'], sizes['pbesparelm'], sizes['pbesstategraph (global)'], sizes['pbesstategraph (local)'], solstr)

def printtime(t):
  if t in ['unknown', 'timeout']:
    return t
  else:
    secs = int(t)
    msecs = int((t - secs)*100)
    msecsstr = str(msecs)[:2]
    if len(msecsstr) == 1:
      msecsstr += '0'
    res = datetime.timedelta(seconds = secs)
    return '{0}.{1}'.format(res, msecsstr)
  
def getrowtimes(data, case, property):
  casedata = data[case][property]
  times = {}
      
  time = casedata.get('original', {}).get('times', {})
  instantiation = time.get('instantiation', {}).get('total', 'unknown')
  solving = time.get('solving', {}).get('total', 'unknown')
  if instantiation == 'timeout' or solving == 'timeout':
    times['original'] = 'timeout'
  elif instantiation == 'unknown' or solving == 'unknown':
    times['original'] = 'unknown'
  else:
    times['original'] = instantiation + solving
  
  for tool in ['pbesparelm', 'pbesstategraph (global)', 'pbesstategraph (local)']:
    time = casedata.get(tool, {}).get('times', {})
    instantiation = time.get('instantiation', {}).get('total', 'unknown')
    reduction = time.get('reduction', {}).get('total', 'unknown')
    solving = time.get('solving', {}).get('total', 'unknown')
    if instantiation == 'timeout' or reduction == 'timeout' or solving == 'timeout':
      times[tool] = 'timeout'
    elif instantiation == 'unknown' or reduction == 'unknown' or solving == 'unknown':
      times[tool] = 'unknown'
    else:
      times[tool] = instantiation + reduction + solving
    
  return ' && {0} && {1} && {2} && {3} &&  \\\\'.format(printtime(times['original']), printtime(times['pbesparelm']), printtime(times['pbesstategraph (global)']), printtime(times['pbesstategraph (local)']))
 

def getrow(data, case, property, times):
  if times:
    return getrowtimes(data, case, property)
  else:
    return getrowsizes(data, case, property)
    

def gettable(data, outfilename, times, log):
  texfile = open(outfilename, 'w')
  
  texfile.write('''\\centering
\\scriptsize
\\begin{tabular}{@{}llrcrcrcrcrrcr@{}}
\\phantom{AB} & & \\phantom{blablabla} & \\phantom{blabla} & Original & & \\texttt{pbesparelm} & & \\texttt{pbesstategraph} & & \\texttt{pbesstategraph} & & verdict\\\\
             & &                     &                  &          & &                     & & \\texttt{(global)}       & & \\texttt{(local)}        & &        \\\\
\\\\[-1ex]
\\toprule
\\\\[-1ex]
& \\multicolumn{5}{c}{Model Checking Problems} \\\\[-1ex]
 \\cmidrule{2-6}  \\\\[-1ex]

\\multicolumn{11}{l}{\\textbf{No deadlock}}  \\\\
''')
  
  texfile.write('  & \\emph{Onebit}   & $|D| = 2$')
  texfile.write(getrow(data, 'Onebit [datasize=2]', 'nodeadlock', times))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 3$')
  texfile.write(getrow(data, 'Onebit [datasize=3]', 'nodeadlock', times))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 4$')
  texfile.write(getrow(data, 'Onebit [datasize=4]', 'nodeadlock', times))
  texfile.write('\n')
  
  texfile.write('  & \\emph{Hesselink}   & $|D| = 2$')
  texfile.write(getrow(data, 'Hesselink [datasize=2]', 'nodeadlock', times))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 3$')
  texfile.write(getrow(data, 'Hesselink [datasize=3]', 'nodeadlock', times))
  texfile.write('\n')
  
  texfile.write('''\\\\[-1ex]
\\multicolumn{11}{l}{\\textbf{No spontaneous generation of messages}}  \\\\
''')

  texfile.write('  & \\emph{Onebit}   & $|D| = 2$')
  texfile.write(getrow(data, 'Onebit [datasize=2]', 'no_spontaneous_messages', times))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 3$')
  texfile.write(getrow(data, 'Onebit [datasize=3]', 'no_spontaneous_messages', times))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 4$')
  texfile.write(getrow(data, 'Onebit [datasize=4]', 'no_spontaneous_messages', times))
  texfile.write('\n')

  texfile.write('''
\\\\[-1ex]
\\multicolumn{11}{l}{\\textbf{Messages that are read are inevitably sent}}  \\\\
''')
  texfile.write('  & \\emph{Onebit}   & $|D| = 2$')
  texfile.write(getrow(data, 'Onebit [datasize=2]', 'messages_read_are_inevitably_sent', times))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 3$')
  texfile.write(getrow(data, 'Onebit [datasize=3]', 'messages_read_are_inevitably_sent', times))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 4$')
  texfile.write(getrow(data, 'Onebit [datasize=4]', 'messages_read_are_inevitably_sent', times))
  texfile.write('\n')    

  texfile.write('''
\\\\[-1ex]
\\multicolumn{11}{l}{\\textbf{Messages can overtake one another}}  \\\\
''')
  texfile.write('  & \\emph{Onebit}   & $|D| = 2$')
  texfile.write(getrow(data, 'Onebit [datasize=2]', 'messages_can_be_overtaken', times))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 3$')
  texfile.write(getrow(data, 'Onebit [datasize=3]', 'messages_can_be_overtaken', times))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 4$')
  texfile.write(getrow(data, 'Onebit [datasize=4]', 'messages_can_be_overtaken', times))
  texfile.write('\n')  

  texfile.write('''
\\\\[-1ex]
\\multicolumn{11}{l}{\\textbf{Values written to the register can be read}} \\\\
''')

  texfile.write('  & \\emph{Hesselink}   & $|D| = 2$')
  texfile.write(getrow(data, 'Hesselink [datasize=2]', 'property2', times))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 3$')
  texfile.write(getrow(data, 'Hesselink [datasize=3]', 'property2', times))
  texfile.write('\n')
  
  texfile.write('''\\\\[-1ex]
& \\multicolumn{5}{c}{Equivalence Checking Problems} \\\\
 \\cmidrule{2-6}  \\\\[-1ex]

\\multicolumn{11}{l}{\\textbf{Branching bisimulation equivalence}} \\\\
''')

  texfile.write('  &  \\emph{ABP-CABP} & $|D| = 2$')
  texfile.write(getrow(data, 'ABP/CABP (datasize=2 capacity=1 windowsize=1)', 'branching-bisim', times))
  texfile.write('\n')
  texfile.write('  &                  & $|D| = 4$')
  texfile.write(getrow(data, 'ABP/CABP (datasize=4 capacity=1 windowsize=1)', 'branching-bisim', times))
  texfile.write('\n')
  
  texfile.write('  &  \\emph{Buf-Onebit} & $|D| = 2$')
  texfile.write(getrow(data, 'Buffer/Onebit (datasize=2 capacity=2 windowsize=1)', 'branching-bisim', times))
  texfile.write('\n')
  texfile.write('  &                  & $|D| = 4$')
  texfile.write(getrow(data, 'Buffer/Onebit (datasize=4 capacity=2 windowsize=1)', 'branching-bisim', times))
  texfile.write('\n')
  
  texfile.write('  & \\emph{Hesselink I-S} & $|D| = 2$')
  texfile.write(getrow(data, 'Hesselink (Implementation)/Hesselink (Specification) (datasize=2)', 'branching-bisim', times))
  texfile.write('\n')
  
  texfile.write('''
\\\\[-1ex]
\\multicolumn{11}{l}{\\textbf{Weak bisimulation equivalence}}  \\\\
''')

  texfile.write('  &  \\emph{ABP-CABP} & $|D| = 2$')
  texfile.write(getrow(data, 'ABP/CABP (datasize=2 capacity=1 windowsize=1)', 'weak-bisim', times))
  texfile.write('\n')
  texfile.write('  &                  & $|D| = 4$')
  texfile.write(getrow(data, 'ABP/CABP (datasize=4 capacity=1 windowsize=1)', 'weak-bisim', times))
  texfile.write('\n')
  
  texfile.write('  &  \\emph{Buf-Onebit} & $|D| = 2$')
  texfile.write(getrow(data, 'Buffer/Onebit (datasize=2 capacity=2 windowsize=1)', 'weak-bisim', times))
  texfile.write('\n')
  texfile.write('  &                  & $|D| = 4$')
  texfile.write(getrow(data, 'Buffer/Onebit (datasize=4 capacity=2 windowsize=1)', 'weak-bisim', times))
  texfile.write('\n')
  
  texfile.write('  & \\emph{Hesselink I-S} & $|D| = 2$')
  texfile.write(getrow(data, 'Hesselink (Implementation)/Hesselink (Specification) (datasize=2)', 'weak-bisim', times))
  texfile.write('\n')

  texfile.write('''
\\\\[-1ex]
\\bottomrule

\\end{tabular}
  ''')

  texfile.close()

  return texfile.name

def run(infilename, outfilename, times, log):
  data = yaml.load(open(infilename).read())
  gettable(data, outfilename, times, log)
  
def runCmdLine():
  parser = optparse.OptionParser(usage='usage: %prog [options] infile outfile')
  parser.add_option('-v', action='count', dest='verbosity',
                    help='Be more verbose. Use more than once to increase verbosity even more.')
  parser.add_option('-t', action='store_true', dest='times',
                    help='Print timing instead of sizes')

  options, args = parser.parse_args()
  if len(args) < 2:
    parser.error(parser.usage)
  
  infilename = args[0]
  outfilename = args[1]

  logging.basicConfig()
  if options.verbosity > 0:
    logging.getLogger('extract').setLevel(logging.INFO)
  
  run(infilename, outfilename, options.times, logging.getLogger('extract'))

if __name__ == '__main__':
  runCmdLine()
