import csv
import logging
import optparse
import os
import re
import sys
import tempfile
import yaml

def addsep(number):
  if number == '??':
    return number
    
  result = '{:,}'.format(int(number))
  return result

def getrow(data, case, property):
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
  

def gettable(data, outfilename, log):
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
  
  texfile.write('  & \emph{Onebit}   & $|D| = 2$')
  texfile.write(getrow(data, 'Onebit [datasize=2]', 'nodeadlock'))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 3$')
  texfile.write(getrow(data, 'Onebit [datasize=3]', 'nodeadlock'))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 4$')
  texfile.write(getrow(data, 'Onebit [datasize=4]', 'nodeadlock'))
  texfile.write('\n')
  
  texfile.write('  & \emph{Hesselink}   & $|D| = 2$')
  texfile.write(getrow(data, 'Hesselink [datasize=2]', 'nodeadlock'))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 3$')
  texfile.write(getrow(data, 'Hesselink [datasize=3]', 'nodeadlock'))
  texfile.write('\n')
  
  texfile.write('''\\[-1ex]
\multicolumn{11}{l}{\textbf{No spontaneous generation of messages}}  \\
''')

  texfile.write('  & \emph{Onebit}   & $|D| = 2$')
  texfile.write(getrow(data, 'Onebit [datasize=2]', 'no_spontaneous_messages'))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 3$')
  texfile.write(getrow(data, 'Onebit [datasize=3]', 'no_spontaneous_messages'))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 4$')
  texfile.write(getrow(data, 'Onebit [datasize=4]', 'no_spontaneous_messages'))
  texfile.write('\n')

  texfile.write('''
\\[-1ex]
\multicolumn{11}{l}{\textbf{Messages that are read are inevitably sent}}  \\
''')
  texfile.write('  & \emph{Onebit}   & $|D| = 2$')
  texfile.write(getrow(data, 'Onebit [datasize=2]', 'messages_read_are_inevitably_sent'))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 3$')
  texfile.write(getrow(data, 'Onebit [datasize=3]', 'messages_read_are_inevitably_sent'))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 4$')
  texfile.write(getrow(data, 'Onebit [datasize=4]', 'messages_read_are_inevitably_sent'))
  texfile.write('\n')    

  texfile.write('''
\\[-1ex]
\multicolumn{11}{l}{\textbf{Messages can overtake one another}}  \\
''')
  texfile.write('  & \emph{Onebit}   & $|D| = 2$')
  texfile.write(getrow(data, 'Onebit [datasize=2]', 'messages_can_be_overtaken'))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 3$')
  texfile.write(getrow(data, 'Onebit [datasize=3]', 'messages_can_be_overtaken'))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 4$')
  texfile.write(getrow(data, 'Onebit [datasize=4]', 'messages_can_be_overtaken'))
  texfile.write('\n')  

  texfile.write('''
\\[-1ex]
\multicolumn{11}{l}{\textbf{Values written to the register can be read}} \\
''')

  texfile.write('  & \emph{Hesselink}   & $|D| = 2$')
  texfile.write(getrow(data, 'Hesselink [datasize=2]', 'property1'))
  texfile.write('\n')
  texfile.write('  &                 & $|D| = 3$')
  texfile.write(getrow(data, 'Hesselink [datasize=3]', 'property1'))
  texfile.write('\n')
  
  texfile.write('''\\[-1ex]
& \multicolumn{5}{c}{Equivalence Checking Problems} \\
 \cmidrule{2-6}  \\[-1ex]

\multicolumn{11}{l}{\textbf{Branching bisimulation equivalence}} \\
''')

  texfile.write('  &  \emph{ABP-CABP} & $|D| = 2$')
  texfile.write(getrow(data, 'ABP/CABP (datasize=2 capacity=1 windowsize=1)', 'branching-bisim'))
  texfile.write('\n')
  texfile.write('  &                  & $|D| = 4$')
  texfile.write(getrow(data, 'ABP/CABP (datasize=4 capacity=1 windowsize=1)', 'branching-bisim'))
  texfile.write('\n')
  
  texfile.write('  &  \emph{Buf-Onebit} & $|D| = 2$')
  texfile.write(getrow(data, 'Buffer/Onebit (datasize=2 capacity=2 windowsize=1)', 'branching-bisim'))
  texfile.write('\n')
  texfile.write('  &                  & $|D| = 4$')
  texfile.write(getrow(data, 'Buffer/Onebit (datasize=4 capacity=2 windowsize=1)', 'branching-bisim'))
  texfile.write('\n')
  
  texfile.write('  & \emph{Hesselink I-S} & $|D| = 2$')
  texfile.write(getrow(data, 'Hesselink (Implementation)/Hesselink (Specification) (datasize=2)', 'branching-bisim'))
  texfile.write('\n')
  
  texfile.write('''
\\[-1ex]
\multicolumn{11}{l}{\textbf{Weak bisimulation equivalence}}  \\
''')

  texfile.write('  &  \emph{ABP-CABP} & $|D| = 2$')
  texfile.write(getrow(data, 'ABP/CABP (datasize=2 capacity=1 windowsize=1)', 'weak-bisim'))
  texfile.write('\n')
  texfile.write('  &                  & $|D| = 4$')
  texfile.write(getrow(data, 'ABP/CABP (datasize=4 capacity=1 windowsize=1)', 'weak-bisim'))
  texfile.write('\n')
  
  texfile.write('  &  \emph{Buf-Onebit} & $|D| = 2$')
  texfile.write(getrow(data, 'Buffer/Onebit (datasize=2 capacity=2 windowsize=1)', 'weak-bisim'))
  texfile.write('\n')
  texfile.write('  &                  & $|D| = 4$')
  texfile.write(getrow(data, 'Buffer/Onebit (datasize=4 capacity=2 windowsize=1)', 'weak-bisim'))
  texfile.write('\n')
  
  texfile.write('  & \emph{Hesselink I-S} & $|D| = 2$')
  texfile.write(getrow(data, 'Hesselink (Implementation)/Hesselink (Specification) (datasize=2)', 'weak-bisim'))
  texfile.write('\n')

  texfile.write('''
\\[-1ex]
\bottomrule

\end{tabular}
  ''')

  texfile.close()

  return texfile.name

def run(infilename, outfilename, log):
  data = yaml.load(open(infilename).read())
  gettable(data, outfilename, log)
  
def runCmdLine():
  parser = optparse.OptionParser(usage='usage: %prog [options] infile outfile')
  parser.add_option('-v', action='count', dest='verbosity',
                    help='Be more verbose. Use more than once to increase verbosity even more.')

  options, args = parser.parse_args()
  if len(args) < 2:
    parser.error(parser.usage)
  
  infilename = args[0]
  outfilename = args[1]

  logging.basicConfig()
  if options.verbosity > 0:
    logging.getLogger('extract').setLevel(logging.INFO)
  
  run(infilename, outfilename, logging.getLogger('extract'))

if __name__ == '__main__':
  runCmdLine()
