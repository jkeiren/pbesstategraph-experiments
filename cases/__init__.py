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
# Memlimit in KBytes
MEMLIMIT = 1*1024*1024

class TempObj(pool.Task):
  def __init__(self, temppath='temp', prefix=""):
    super(TempObj, self).__init__()
    self._temppath = temppath
    self._prefix = prefix

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
  def __init__(self, name, prefix, filename):
    super(ReduceAndSolveTask, self).__init__()
    self.__pbesfile = filename
    self._prefix = prefix
    if name.startswith('pbesparelm'):
      self.__reducedPbesfile = self._newTempFilename('pbes', 'parelm.constelm')
      self.__besfile = self._newTempFilename('bes', '.parelm.constelm')
    else:
      self.__reducedPbesfile = self._newTempFilename('pbes', '.stategraph.constelm')
      self.__besfile = self._newTempFilename('bes', '.stategraph.constelm')
    self.name = name
    self.result = {}
    self.result['name'] = self.name
    self.result['times'] = {}
    self.result['sizes'] = 'unknown'
  
  def __reduce(self, log):
    log.debug('Creating temp files')
    if self.name.startswith('pbesparelm'):
      tmpfile = self._newTempFilename('pbes', '.parelm')
    else:
      tmpfile = self._newTempFilename('pbes', '.stategraph')
    
    try:
      if self.name.startswith('pbesparelm'):
        log.debug('Parelm')
        result = tools.pbesparelm(self.__pbesfile, tmpfile, timed=True, timeout=REDUCTION_TIMEOUT, memlimit=MEMLIMIT)
      else:
        log.debug('Stategraph')
        result = tools.pbesstategraph(self.__pbesfile, tmpfile, timed=True, timeout=REDUCTION_TIMEOUT, memlimit=MEMLIMIT)
       
      self.result['times']['reduction'] = result['times']

      result = tools.pbesconstelm(tmpfile, self.__reducedPbesfile, timed=True)
       
    except (tools.Timeout):
      log.info('Timeout')
      self.times['reduction'] = 'timeout'
      raise tools.Timeout()

    
  def __instantiate(self, log):
    result = tools.pbes2bes('-rjittyc', self.__reducedPbesfile, self.__besfile, timed=True)
    self.result['times']['instantiation'] = result['times']
    
    info = tools.besinfo(self.__besfile, '-v', memlimit=MEMLIMIT)['out']
    BESINFO_RE = '.*Number of equations:\s*(?P<eqns>\d+)' \
             '.*Number of mu.?s:\s*(?P<mueqns>\d+)' \
             '.*Number of nu.?s:\s*(?P<nueqns>\d+)' \
             '.*Block nesting depth:\s*(?P<bnd>\d+).*?'
    m = re.search(BESINFO_RE, info, re.DOTALL)
    self.result['sizes'] = m.groupdict()
  
  def __solve(self, log):
    try:      
      result = tools.pbespgsolve(self.__besfile, timed=True, timeout=SOLVE_TIMEOUT, memlimit=MEMLIMIT)
      self.result['times']['solving'] = result['times']      
      self.result['solution'] = result['out'].strip()
    except (tools.Timeout):
      log.info('Timeout')
      self.result['times']['solving'] = 'timeout'
      self.result['solution'] = 'unknown'
  
  def phase0(self, log):
    log.info('Reducing PBES')
    timeout = False
    try:
      self.__reduce(log)
    except (tools.Timeout):
      self.result['times']['solving'] = 'timeout'
      self.result['times']['instantiation'] = 'timeout'
      self.result['solution'] = 'unknown'
      self.result['sizes'] = 'unknown'
      timeout = True

    if not timeout:
      log.info('Instantiating PBES')
      self.__instantiate(log)
      log.info('Solving PBES')
      self.__solve(log)
  
class PBESCase(TempObj):
  def __init__(self, temppath='temp', prefix=""):
    super(PBESCase, self).__init__(temppath, prefix)
    self.__pbesfile = self._newTempFilename('pbes')
    self.result = {}
  
  def _makePBES(self):
    raise NotImplementedError()
  
  def _writePBESfile(self, log):
    pbes = self._makePBES()
    tmp = tools.pbesrewr('-psimplify', stdin=pbes, memlimit=MEMLIMIT)
    tmp = tools.pbesrewr('-pquantifier-one-point', stdin=tmp['out'], memlimit=MEMLIMIT)
    tmp = tools.pbesrewr('-psimplify', stdin=tmp['out'], memlimit=MEMLIMIT)
    tmp = tools.pbesconstelm(stdin=tmp['out'], memlimit=MEMLIMIT)

    log.debug("Writing PBES")
    pbes = open(self.__pbesfile, 'w')
    pbes.write(tmp['out'])
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
      self.result[task.name] = task.result
    
