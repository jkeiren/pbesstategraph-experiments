import tempfile
import logging
import traceback
import multiprocessing
import os
from cases import tools, PBESCase, TempObj, MEMLIMIT

class EquivCase(PBESCase):
  def __init__(self, description, lpsfile1, lpsfile2, equiv, temppath):
    super(EquivCase, self).__init__()
    self.__desc = description
    self._temppath = temppath
    self._prefix = self.__desc + "eq=%s" % (equiv)
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
    #log.info('Applying lpssuminst to LPSs for {0}'.format(self))
    #lps1 = tools.lpssuminst('-f', stdin=lps1, memlimit=MEMLIMIT)['out']
    #lps2 = tools.lpssuminst('-f', stdin=lps2, memlimit=MEMLIMIT)['out']
    lpsfile1 = self._newTempFile('lps')
    lpsfile1.write(lps1)
    lpsfile1.close()
    lpsfile2 = self._newTempFile('lps')
    lpsfile2.write(lps2)
    lpsfile2.close()
    return lpsfile1.name, lpsfile2.name
  
  def phase0(self, log):
    lpsfile1, lpsfile2 = self.__linearise(log)
    #for equiv in ['strong-bisim', 'weak-bisim', 'branching-bisim', 'branching-sim']:
    for equiv in ['strong-bisim']:
      self.subtasks.append(EquivCase(self.__desc, lpsfile1, lpsfile2, equiv, self._temppath))
    self.__files = [lpsfile1, lpsfile2]
  
  def phase1(self, log):
    log.info('Finalising {0}'.format(self))
    for case in self.results:
      self.result[str(case)] = case.result
    for filename in self.__files:
      os.unlink(filename)
  
def getcases(debug):
  import specs
  buf = specs.get('Buffer')
  abp = specs.get('ABP')
  swp = specs.get('SWP')
  if debug:
    return \
      [Case('SWP/Buffer (w={0}, d={1})'.format(1, 2), swp.mcrl2(1, 2), buf.mcrl2(2 * 1, 2))] +\
      [Case('ABP/ABP (d={0})'.format(2), abp.mcrl2(2), abp.mcrl2(2))] +\
      [Case('SWP/ABP (w={0}, d={1})'.format(1, 2), swp.mcrl2(1, 2), abp.mcrl2(2))]
  else:
    return \
      [Case('SWP/Buffer (w={0}, d={1})'.format(w, d), swp.mcrl2(w, d), buf.mcrl2(2 * w, d))
        for w, d in [(1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (2, 2), (2, 3)]] + \
      [Case('ABP/ABP (d={1})'.format(d), abp.mcrl2(d), abp.mcrl2(d))
       for d in [2, 3, 4, 5, 6, 7, 8, 16, 32]] + \
      [Case('SWP/ABP (w={0}, d={1})'.format(w, d), swp.mcrl2(w, d), abp.mcrl2(d))
       for w, d in [(1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (2, 2), (2, 3)]]
