import tempfile
import logging
import traceback
import multiprocessing
import os
from cases import tools, PBESCase, TempObj, MEMLIMIT

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
    #for filename in self.__files:
    #  os.unlink(filename)
  
def getcases(debug):
  import specs
  buf = specs.get('Buffer')
  abp = specs.get('ABP')
  abp_bw = specs.get('ABP(BW)')
  cabp = specs.get('CABP')
  par = specs.get('Par')
  onebit = specs.get('Onebit')
  swp = specs.get('SWP')
  hesselink_spec = specs.get('Hesselink (Specification)')
  hesselink = specs.get('Hesselink (Implementation)')
  if debug:
    return \
      [Case('Hesselink (Implementation)/Hesselink (Specification) (d={0})'.format(d), hesselink_spec.mcrl2(d), hesselink.mcrl2(d))
         for d in range(2,3)] + \
      [Case('Buffer/ABP (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), abp.mcrl2(w,c,d))
         for (w,c,d) in [(1,1,2)]] + \
      [Case('Buffer/ABP(BW) (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), abp_bw.mcrl2(w,c,d))
         for (w,c,d) in [(1,1,2)]] + \
      [Case('Buffer/CABP (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), cabp.mcrl2(w,c,d))
         for (w,c,d) in [(1,1,2)]] + \
      [Case('Buffer/Par (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), par.mcrl2(w,c,d))
         for (w,c,d) in [(1,1,2)]] + \
      [Case('Buffer/Onebit (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), onebit.mcrl2(w,c,d))
         for (w,c,d) in [(1,2,2)]] + \
      [Case('Buffer/SWP (w={0}, c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), swp.mcrl2(w,c,d))
         for (w,c,d) in [(1,2,2)]] + \
      [Case('ABP/ABP (d={2})'.format(w,c,d), abp.mcrl2(w,c,d), abp.mcrl2(w,c,d))
         for (w,c,d) in [(1,2,2)]] + \
      [Case('ABP/SWP (w={0}, d={2})'.format(w,c,d), abp.mcrl2(w,c,d), swp.mcrl2(w,c,d))
         for (w,c,d) in [(1,2,2)]]
  else:
    return \
      [Case('Buffer/ABP (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), abp.mcrl2(w,c,d))
         for (w,c,d) in [(1,1,2)]] + \
      [Case('Buffer/ABP(BW) (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), abp_bw.mcrl2(w,c,d))
         for (w,c,d) in [(1,1,2)]] + \
      [Case('Buffer/CABP (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), cabp.mcrl2(w,c,d))
         for (w,c,d) in [(1,1,2)]] + \
      [Case('Buffer/Par (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), par.mcrl2(w,c,d))
         for (w,c,d) in [(1,1,2)]] + \
      [Case('Buffer/Onebit (c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), onebit.mcrl2(w,c,d))
         for (w,c,d) in [(1,2,2)]] + \
      [Case('Buffer/SWP (w={0}, c={1}, d={2})'.format(w,c,d), buf.mcrl2(w,c,d), swp.mcrl2(w,c,d))
         for (w,c,d) in [(1,2,data) for data in range(2,9)] + [(2,4,data) for data in range(2,4)]] + \
      [Case('ABP/ABP (d={2})'.format(w,c,d), abp.mcrl2(w,c,d), abp.mcrl2(w,c,d))
         for (w,c,d) in [(1,2,data) for data in [2, 3, 4, 5, 6, 7, 8, 16, 32] ]] + \
      [Case('ABP/SWP (w={0}, d={2})'.format(w,c,d), abp.mcrl2(w,c,d), swp.mcrl2(w,c,d))
         for (w,c,d) in [(1,2,data) for data in range(2,9)] + [(2,4,data) for data in range(2,4)]] + \
      [Case('Hesselink (Implementation)/Hesselink (Specification) (d={0})'.format(d), hesselink_spec.mcrl2(d), hesselink.mcrl2(d))
         for d in range(2,5)]
      
