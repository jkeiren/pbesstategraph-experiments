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

def printsize(sizes, tool, percentages):
  if percentages and tool != 'original' and sizes['original'] != '??' and sizes[tool] != '??':
      return '{0:.0f}\%'.format(((float(sizes['original'])-float(sizes[tool]))/float(sizes['original'])) * 100)
  else:
      return addsep(sizes[tool])

def printtime(times, tool, percentages, msecs=False):
  if percentages and tool != 'original' and times['original'] != 'unknown' and times[tool] != 'unknown':
    return '{0:.0f}\%'.format(((times['original']-times[tool])/times['original']) * 100)
  elif times[tool] in ['unknown', 'timeout']:
    return times[tool]
  else:
    secs = int(times[tool])
    res = datetime.timedelta(seconds = secs)
    
    if msecs:
      msecs = int((times[tool] - secs)*100)
      msecsstr = str(msecs)[:2]
      if len(msecsstr) == 1:
        msecsstr += '0'
      return '{0}.{1}'.format(res, msecsstr)

    else:
      return '{0:.1f}'.format(times[tool])#str(res)
  

def getrow(data, case, property, reportsizes, reporttimes, reportsolution, percentages):
  casedata = data[case][property]
  
  solutions = {}
  result = ''
  
  sizes = {}
  # Get sizes
  for tool in ['original', 'pbesparelm', 'pbesstategraph (global)', 'pbesstategraph (local)']:
    size = casedata.get(tool, {}).get('sizes', {})
    if size == 'unknown':
      size = {}
    sizes[tool] = size.get('eqns', '??')
    if sizes[tool] != '??':
      sizes[tool] = int(sizes[tool])

    solutions[tool] = casedata.get(tool, {}).get('solution', 'unknown')

  if sizes['pbesstategraph (global)'] > sizes['pbesstategraph (local)']:
    print 'Warning, {0} -- {1} has global stategraph > local stategraph ({2} > {3})'.format(case, property, sizes['pbesstategraph (global)'], sizes['pbesstategraph (local)'])

  times = {}
  time = casedata.get('original', {})
  if isinstance(time, dict):
    time = time.get('times', {})
  else:
    time = {}
  instantiation = time.get('instantiation', {})
  if isinstance(instantiation, dict):
    instantiation = instantiation.get('total', 'unknown')

  solving = time.get('solving', {}).get('total', 'unknown')
  if instantiation == 'timeout' or solving == 'timeout':
    times['original'] = 'timeout'
  elif instantiation == 'unknown' or solving == 'unknown':
    times['original'] = 'unknown'
  else:
    times['original'] = instantiation + solving
  
  for tool in ['pbesparelm', 'pbesstategraph (global)', 'pbesstategraph (local)']:
    time = casedata.get(tool, {})
    if isinstance(time, dict):
      time = time.get('times', {})
    else:
      time = {}
    
    instantiation = time.get('instantiation', {})
    if isinstance(instantiation, dict):
      instantiation = instantiation.get('total', 'unknown')
    
    reduction = time.get('reduction', {})
    if isinstance(reduction, dict):
      reduction = reduction.get('total', 'unknown')
    
    solving = time.get('solving', {})
    if isinstance(solving, dict):
      solving = solving.get('total', 'unknown')
    if instantiation == 'timeout' or reduction == 'timeout' or solving == 'timeout':
      times[tool] = 'timeout'
    elif instantiation == 'unknown' or reduction == 'unknown' or solving == 'unknown':
      times[tool] = 'unknown'
    else:
      times[tool] = instantiation + reduction + solving

  if reportsizes:
    result += ' & {0} & {1} & {2} & {3}'.format(printsize(sizes, 'original', percentages),
      printsize(sizes, 'pbesparelm', percentages),
      printsize(sizes, 'pbesstategraph (global)', percentages),
      printsize(sizes, 'pbesstategraph (local)', percentages))

  if reporttimes:
    result += ' & {0} & {1} & {2} & {3}'.format(printtime(times, 'original', percentages),
      printtime(times, 'pbesparelm', percentages),
      printtime(times, 'pbesstategraph (global)', percentages),
      printtime(times, 'pbesstategraph (local)', percentages))
  
  if reportsolution:
    sol = '??'
    for v in solutions.values():
      if v != 'unknown':
        if v not in ['true', 'false']:
          print "Unexpected solution for {0}, {1}"
          continue
          
        if sol != '??' and v != sol:
          print "Different solutions for {0}, {1}".format(case, property)
        sol = v

    if sol == 'true':
      solstr = '\\surd'
    elif sol == 'false':
      solstr = '\\times'
    else:
      solstr = sol

    result += ' & ${0}$'.format(solstr)
    
  return '{0} \\\\'.format(result)
 


def gettable(data, outfilename, sizes, times, solution, percentages):
  print 'Getting table, sizes: {0}, times: {1}, solution: {2}'.format(sizes, times, solution, percentages)
  texfile = open(outfilename, 'w')

  columns = 3
  if sizes:
    columns += 9
  if times:
    columns += 9
  if solution:
    columns += 2

  # - & Case & size & - & Original & blank & parelm & blank & stategraph & blank & stategraph & blank & solution
  
  texfile.write('''\\centering
\\scriptsize
''')
  texfile.write('\\begin{{tabular}}{{lc@{{\\hspace{{5pt}}}}|@{{\\hspace{{5pt}}}}{0}{1}{2}@{{}}}}'.format('rrrr' if sizes else '', '@{\\hspace{5pt}}|@{\\hspace{5pt}}rrrr' if times else '', '@{\\hspace{5pt}}|@{\\hspace{5pt}}c' if solution else ''))
#  texfile.write(
  texfile.write(' & {0}{1}{2}\\\\'.format(' & \\multicolumn{4}{c}{Sizes}' if sizes else '',  ' & \\multicolumn{4}{c}{Times}' if times else '', '&' if solution else ''))
  texfile.write(' & $|D|$ {0}{1}{2}\\\\'.format(' & Original & \\texttt{parelm} & \\texttt{st.graph} & \\texttt{st.graph}' if sizes else '',
    ' & Original & \\texttt{parelm} & \\texttt{st.graph} & \\texttt{st.graph}' if times else '',
    ' & verdict' if solution else ''))
  texfile.write('             &   {0}{1}{2}\\\\'.format('&&& \\texttt{(global)}  & \\texttt{(local)} ' if sizes else '', '&&& \\texttt{(global)}  & \\texttt{(local)}' if times else '', '& ' if solution else ''))
  texfile.write('''
\\\\[-1ex]
\\toprule
\\\\[-1ex]
 \\multicolumn{4}{c}{Model Checking Problems} \\\\
 \\cmidrule{1-4}  \\\\[-1ex]

\\multicolumn{11}{l}{\\textbf{No deadlock}}  \\\\
''')
  
  texfile.write('\\emph{Onebit}   & $2$')
  texfile.write(getrow(data, 'Onebit [datasize=2]', 'nodeadlock', sizes, times, solution, percentages))
  texfile.write('\n')
  texfile.write('                 & $3$')
  texfile.write(getrow(data, 'Onebit [datasize=3]', 'nodeadlock', sizes, times, solution, percentages))
  texfile.write('\n')
  texfile.write('                 & $4$')
  texfile.write(getrow(data, 'Onebit [datasize=4]', 'nodeadlock', sizes, times, solution, percentages))
  texfile.write('\n')
  
  texfile.write('\\emph{Hesselink} & $2$')
  texfile.write(getrow(data, 'Hesselink [datasize=2]', 'nodeadlock', sizes, times, solution, percentages))
  texfile.write('\n')
  texfile.write('                  & $3$')
  texfile.write(getrow(data, 'Hesselink [datasize=3]', 'nodeadlock', sizes, times, solution, percentages))
  texfile.write('\n')
  
  texfile.write('''\\\\[-1ex]
\\multicolumn{11}{l}{\\textbf{No spontaneous generation of messages}}  \\\\
''')

  texfile.write('\\emph{Onebit}  & $2$')
  texfile.write(getrow(data, 'Onebit [datasize=2]', 'no_spontaneous_messages', sizes, times, solution, percentages))
  texfile.write('\n')
  texfile.write('                & $3$')
  texfile.write(getrow(data, 'Onebit [datasize=3]', 'no_spontaneous_messages', sizes, times, solution, percentages))
  texfile.write('\n')
  texfile.write('                & $4$')
  texfile.write(getrow(data, 'Onebit [datasize=4]', 'no_spontaneous_messages', sizes, times, solution, percentages))
  texfile.write('\n')

  texfile.write('''
\\\\[-1ex]
\\multicolumn{11}{l}{\\textbf{Messages that are read are inevitably sent}}  \\\\
''')
  texfile.write('\\emph{Onebit}  & $2$')
  texfile.write(getrow(data, 'Onebit [datasize=2]', 'messages_read_are_inevitably_sent', sizes, times, solution, percentages))
  texfile.write('\n')
  texfile.write('                & $3$')
  texfile.write(getrow(data, 'Onebit [datasize=3]', 'messages_read_are_inevitably_sent', sizes, times, solution, percentages))
  texfile.write('\n')
  texfile.write('                & $4$')
  texfile.write(getrow(data, 'Onebit [datasize=4]', 'messages_read_are_inevitably_sent', sizes, times, solution, percentages))
  texfile.write('\n')    

  texfile.write('''
\\\\[-1ex]
\\multicolumn{11}{l}{\\textbf{Messages can overtake one another}}  \\\\
''')
  texfile.write('\\emph{Onebit} & $2$')
  texfile.write(getrow(data, 'Onebit [datasize=2]', 'messages_can_be_overtaken', sizes, times, solution, percentages))
  texfile.write('\n')
  texfile.write('               & $3$')
  texfile.write(getrow(data, 'Onebit [datasize=3]', 'messages_can_be_overtaken', sizes, times, solution, percentages))
  texfile.write('\n')
  texfile.write('               & $4$')
  texfile.write(getrow(data, 'Onebit [datasize=4]', 'messages_can_be_overtaken', sizes, times, solution, percentages))
  texfile.write('\n')  

  texfile.write('''
\\\\[-1ex]
\\multicolumn{11}{l}{\\textbf{Values written to the register can be read}} \\\\
''')

  texfile.write(' \\emph{Hesselink} & $2$')
  texfile.write(getrow(data, 'Hesselink [datasize=2]', 'property2', sizes, times, solution, percentages))
  texfile.write('\n')
  texfile.write('                 & $3$')
  texfile.write(getrow(data, 'Hesselink [datasize=3]', 'property2', sizes, times, solution, percentages))
  texfile.write('\n')
  
  texfile.write('''\\\\[-1ex]
 \\multicolumn{4}{c}{Equivalence Checking Problems} \\\\
 \\cmidrule{1-4}  \\\\[-1ex]

\\multicolumn{11}{l}{\\textbf{Branching bisimulation equivalence}} \\\\
''')

  texfile.write('\\emph{ABP-CABP} & $2$')
  texfile.write(getrow(data, 'ABP/CABP (datasize=2 capacity=1 windowsize=1)', 'branching-bisim', sizes, times, solution, percentages))
  texfile.write('\n')
  texfile.write('                 & $4$')
  texfile.write(getrow(data, 'ABP/CABP (datasize=4 capacity=1 windowsize=1)', 'branching-bisim', sizes, times, solution, percentages))
  texfile.write('\n')
  
  texfile.write('\\emph{Buf-Onebit} & $2$')
  texfile.write(getrow(data, 'Buffer/Onebit (datasize=2 capacity=2 windowsize=1)', 'branching-bisim', sizes, times, solution, percentages))
  texfile.write('\n')
  texfile.write('                   & $4$')
  texfile.write(getrow(data, 'Buffer/Onebit (datasize=4 capacity=2 windowsize=1)', 'branching-bisim', sizes, times, solution, percentages))
  texfile.write('\n')
  
  texfile.write('\\emph{Hesselink I-S} & $2$')
  texfile.write(getrow(data, 'Hesselink (Implementation)/Hesselink (Specification) (datasize=2)', 'branching-bisim', sizes, times, solution, percentages))
  texfile.write('\n')
  
  texfile.write('''
\\\\[-1ex]
\\multicolumn{11}{l}{\\textbf{Weak bisimulation equivalence}}  \\\\
''')

  texfile.write('\\emph{ABP-CABP} & $2$')
  texfile.write(getrow(data, 'ABP/CABP (datasize=2 capacity=1 windowsize=1)', 'weak-bisim', sizes, times, solution, percentages))
  texfile.write('\n')
  texfile.write('                 & $4$')
  texfile.write(getrow(data, 'ABP/CABP (datasize=4 capacity=1 windowsize=1)', 'weak-bisim', sizes, times, solution, percentages))
  texfile.write('\n')
  
  texfile.write('\\emph{Buf-Onebit} & $2$')
  texfile.write(getrow(data, 'Buffer/Onebit (datasize=2 capacity=2 windowsize=1)', 'weak-bisim', sizes, times, solution, percentages))
  texfile.write('\n')
  texfile.write('                   & $4$')
  texfile.write(getrow(data, 'Buffer/Onebit (datasize=4 capacity=2 windowsize=1)', 'weak-bisim', sizes, times, solution, percentages))
  texfile.write('\n')
  
  texfile.write('\\emph{Hesselink I-S} & $2$')
  texfile.write(getrow(data, 'Hesselink (Implementation)/Hesselink (Specification) (datasize=2)', 'weak-bisim', sizes, times, solution, percentages))
  texfile.write('\n')

  texfile.write('''
\\\\[-1ex]
\\bottomrule

\\end{tabular}
  ''')

  texfile.close()

  return texfile.name
 
  
def runCmdLine():
  parser = optparse.OptionParser(usage='usage: %prog [options] infile outfile')
  parser.add_option('-t', action='store_true', dest='times',
                    help='Print timing instead of sizes')
  parser.add_option('-p', action='store_true', dest='percentages',
                    help='Print data of reduced PBESs in percentages, relative to original')

  options, args = parser.parse_args()
  if len(args) < 2:
    parser.error(parser.usage)
  
  infilename = args[0]
  outfilename = args[1]

  data = yaml.load(open(infilename).read())
  gettable(data, outfilename, sizes = True, times = options.times, solution = True, percentages = options.percentages)

if __name__ == '__main__':
  runCmdLine()
