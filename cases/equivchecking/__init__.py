import logging
import multiprocessing
import os
import tempfile
import traceback

from cases import tools, PBESCase, TempObj, MEMLIMIT, CLEANUP
import specs

class EquivCase(PBESCase):
  def __init__(self, description, lpsfile1, lpsfile2, equiv, temppath):
    super(EquivCase, self).__init__(temppath = temppath, prefix = description + "eq={0}".format(equiv))
    self.__desc = description
    self.lpsfile1 = lpsfile1
    self.lpsfile2 = lpsfile2
    self.equiv = equiv
    
  def __str__(self):
    return self.equiv
  
  def _makePBES(self):
    pbes = tools.lpsbisim2pbes('-b' + self.equiv, self.lpsfile1, self.lpsfile2, memlimit=MEMLIMIT)['out']
    return tools.pbesconstelm(stdin=pbes, memlimit=MEMLIMIT)['out']
  
class Case(TempObj):
  def __init__(self, description, spec1, spec2):
    super(Case, self).__init__()
    self.__desc = description
    self.__files = []
    self._temppath = os.path.join(os.path.split(__file__)[0], 'temp')
    self._prefix = self.__desc
    self.spec1 = spec1
    self.spec2 = spec2
    self.result = {}
  
  def __str__(self):
    return self.__desc

  def __linearise(self, log):
    '''Linearises self.spec1 and self.spec2 and applies lpssuminst to the 
       resulting LPSs.'''
    log.info('Linearising LPSs for {0}'.format(self))
    lps1 = tools.mcrl22lps('-fn', stdin=self.spec1, memlimit=MEMLIMIT)['out']
    lps2 = tools.mcrl22lps('-fn', stdin=self.spec2, memlimit=MEMLIMIT)['out']
    lpsfile1 = self._newTempFile('lps')
    lpsfile1.write(lps1)
    lpsfile1.close()
    lpsfile2 = self._newTempFile('lps')
    lpsfile2.write(lps2)
    lpsfile2.close()
    return lpsfile1.name, lpsfile2.name
  
  def phase0(self, log):
    lpsfile1, lpsfile2 = self.__linearise(log)
    for equiv in ['strong-bisim', 'weak-bisim', 'branching-bisim', 'branching-sim']:
    #for equiv in ['strong-bisim']:
      self.subtasks.append(EquivCase(self.__desc, lpsfile1, lpsfile2, equiv, self._temppath))
    self.__files = [lpsfile1, lpsfile2]
  
  def phase1(self, log):
    log.info('Finalising {0}'.format(self))
    for case in self.results:
      self.result[str(case)] = case.result
      
    if CLEANUP:
      for filename in self.__files:
        os.unlink(filename)
 
class SameParamCase(Case):
  def __init__(self, name1, name2, **kwargs):
    super(SameParamCase, self).__init__(
      '{0}/{1} ({2})'.format(name1, name2, ' '.join('{0}={1}'.format(k,v) for k,v in kwargs.items())),
      specs.get(name1).mcrl2(**kwargs),
      specs.get(name2).mcrl2(**kwargs)) 

def getcases(debug):
  if debug:
    return \
      [SameParamCase('Buffer', 'ABP', windowsize=1, capacity=1, datasize=2)]
     
  else:
    datarange = range(4,5)
    return \
      [SameParamCase('Buffer', 'ABP', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('Buffer', 'ABP(BW)', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('Buffer', 'CABP', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('Buffer', 'Par', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('Buffer', 'Onebit', windowsize=1, capacity=c, datasize=d) for d in datarange for c in range(1,3)] + \
      [SameParamCase('Buffer', 'SWP', windowsize=1, capacity=c, datasize=d) for d in datarange for c in range(1,3)] + \
      [SameParamCase('ABP', 'ABP', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('ABP', 'ABP(BW)', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('ABP', 'CABP', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('ABP', 'Par', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('ABP', 'Onebit', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('ABP', 'SWP', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('ABP(BW)', 'ABP(BW)', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('ABP(BW)', 'CABP', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('ABP(BW)', 'Par', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('ABP(BW)', 'Onebit', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('ABP(BW)', 'SWP', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('CABP', 'Par', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('CABP', 'Onebit', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('CABP', 'SWP', windowsize=1, capacity=1, datasize=d) for d in datarange] + \
      [SameParamCase('Par', 'Par', windowsize=1, capacity=1, datasize=d) for d in range(4,5)] + \
      [SameParamCase('Par', 'Onebit', windowsize=1, capacity=1, datasize=d) for d in range(4,5)] + \
      [SameParamCase('Par', 'SWP', windowsize=1, capacity=1, datasize=d) for d in range(4,5)] + \
      [SameParamCase('Onebit', 'Onebit', windowsize=1, capacity=1, datasize=d) for d in range(4,5)] + \
      [SameParamCase('Onebit', 'SWP', windowsize=1, capacity=1, datasize=d) for d in range(4,5)] + \
      [SameParamCase('SWP', 'SWP', windowsize=1, capacity=1, datasize=d) for d in range(4,5)] + \
      [SameParamCase('Hesselink (Specification)', 'Hesselink (Implementation)', datasize=d) for d in range(2,5) ] + \
      [SameParamCase('Hesselink (Implementation)', 'Hesselink (Specification)', datasize=d) for d in range(2,5) ]
  