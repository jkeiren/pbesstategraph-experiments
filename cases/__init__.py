import multiprocessing
import logging
import traceback
import tempfile
import os
import re
import tools
import pool
import sys

SOLVE_TIMEOUT = 3600
REDUCTION_TIMEOUT = 900

class TempObj(pool.Task):
  def __init__(self):
    super(TempObj, self).__init__()
    self._temppath = 'temp'
    self._prefix = ""

  def __escape(self, s):
    return s.replace('/', '_').replace(' ', '_')
    
  def _newTempFile(self, ext, extraprefix=""):
    if not os.path.exists(self._temppath):
      os.makedirs(self._temppath)
    name = self._temppath + '/' + self.__escape(self._prefix) + extraprefix + '.' + ext
    if self._prefix <> "" and not os.path.exists(name):
      fn = open(name, 'w+b')
      return fn
    else:
      return tempfile.NamedTemporaryFile(dir=self._temppath, prefix=self.__escape(self._prefix)+extraprefix, suffix='.'+ext, delete=False)
    
  def _newTempFilename(self, ext, extraprefix=""):
    fn = self._newTempFile(ext, extraprefix)
    fn.close()
    return fn.name

class ReduceAndSolveTask(TempObj):
  def __init__(self, name, prefix, filename, *args):
    super(ReduceAndSolveTask, self).__init__()
    self.__pbesfile = filename
    if name.startswith('pbesparelm'):
      self.__reducedPbesfile = self._newTempFilename('pbes', 'constelm.parelm.constelm')
      self.__besfile = self._newTempFilename('bes', 'parelm')
    else:
      self.__reducedPbesfile = self._newTempFilename('pbes', 'constelm.stategraph.constelm')
      self.__besfile = self._newTempFilename('bes', 'stategraph')
    self.__opts = list(args)
    self._prefix = prefix
    self.name = name
    self.times = {}
    self.sizes = 'error'
    self.result = None
  
  def __reduce(self, log):
    log.debug('Creating temp files')
    tmpfile1 = self._newTempFilename('pbes', 'constelm')
    if self.name.startswith('pbesparelm'):
      tmpfile2 = self._newTempFilename('pbes','constelm.parelm')
    else:
      tmpfile2 = self._newTempFilename('pbes', 'constelm.stategraph')
    
    log.debug('Constelm')
    result, t = tools.pbesconstelm(self.__pbesfile, tmpfile1, *self.__opts, timed=True)
    self.times['reduction'] = t[0]['timing']['total'] 
    
    try:
      if self.name.startswith('pbesparelm'):
        log.debug('Parelm')
        result, t = tools.pbesparelm(tmpfile1, tmpfile2, *self.__opts, timed=True, timeout=REDUCTION_TIMEOUT)
      else:
        log.debug('Stategraph')
        result, t = tools.pbesstategraph(tmpfile1, tmpfile2, *self.__opts, timed=True, timeout=REDUCTION_TIMEOUT)
      self.times['reduction'] += t[0]['timing']['total']

      log.debug('Constelm again')
      result, t = tools.pbesconstelm(tmpfile2, self.__reducedPbesfile, timed=True)
      self.times['reduction'] += t[0]['timing']['total'] 
    except (tools.Timeout):
      log.info('Timeout')
      self.times['reduction'] = 'timeout'
      raise tools.Timeout()

    
  def __instantiate(self, log):
    result, t = tools.pbes2bes('-rjittyc', self.__reducedPbesfile, self.__besfile, timed=True)
    self.times['instantiation'] = t[0]['timing']['total']
    info = tools.besinfo(self.__besfile, '-v')
    BESINFO_RE = '.*Number of equations:\s*(?P<eqns>\d+)' \
             '.*Number of mu.?s:\s*(?P<mueqns>\d+)' \
             '.*Number of nu.?s:\s*(?P<nueqns>\d+)' \
             '.*Block nesting depth:\s*(?P<bnd>\d+).*?'
    m = re.search(BESINFO_RE, info, re.DOTALL)
    self.sizes = m.groupdict()
  
  def __solve(self, log):
    try:      
      result, t = tools.pbespgsolve(self.__besfile, *self.__opts, timed=True, timeout=SOLVE_TIMEOUT)
      self.times['solving'] = t[0]['timing']['solving']      
      self.result = result.strip()
    except (tools.Timeout):
      log.info('Timeout')
      self.times['solving'] = 'timeout'
      self.result = 'unknown'
  
  def phase0(self, log):
    log.info('Reducing PBES')
    timeout = False
    try:
      self.__reduce(log)
    except (tools.Timeout):
      self.times['solving'] = 'timeout'
      self.times['instantiation'] = 'timeout'
      self.result = 'unknown'
      self.sizes = 'unknown'
      timeout = True

    if not timeout:
      log.info('Instantiating PBES')
      self.__instantiate(log)
      log.info('Solving PBES')
      self.__solve(log)
  
class PBESCase(TempObj):
  def __init__(self):
    super(PBESCase, self).__init__()
    self.__pbesfile = self._newTempFilename('pbes')
    self.sizes = {}
    self.times = {}
    self.solutions = {}
  
  def _makePBES(self):
    raise NotImplementedError()
  
  def _writePBESfile(self, log):
    tmp = self._makePBES()
    tmp = tools.pbesrewr('-psimplify', stdin=tmp)
    tmp = tools.pbesrewr('-pquantifier-one-point', stdin=tmp)
    tmp = tools.pbesrewr('-psimplify', stdin=tmp)

    log.debug("Writing PBES")
    pbes = open(self.__pbesfile, 'w')
    pbes.write(tmp)
    pbes.close()
    
  def __reduce(self, pbesfile, log):
    log.debug('Reduction...')
    self.subtasks = [ 
      ReduceAndSolveTask('pbesparelm', self._prefix, pbesfile),
      ReduceAndSolveTask('pbesstategraph', self._prefix, pbesfile),
    ]
    
  def phase0(self, log):
    log.debug('Generating initial PBES')
    self._writePBESfile(log)
    log.debug('Reducing PBES and instantiating and solving')
    self.__reduce(self.__pbesfile, log)    
    
  def phase1(self, log):
    for task in self.results:
      self.sizes[task.name] = task.sizes
      self.times[task.name] = task.times
      self.solutions[task.name] = task.result
    
