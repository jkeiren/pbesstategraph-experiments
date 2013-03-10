import multiprocessing
import logging
import traceback
import tempfile
import os
import re
import tools
import pool
import sys

GENERATE_TIMEOUT = 2*60*60
SOLVE_TIMEOUT = 60*60
REDUCTION_TIMEOUT = 15*60
# Memlimit in KBytes
MEMLIMIT = 64*1024*1024

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
  def __init__(self, name, prefix, filename, temppath):
    super(ReduceAndSolveTask, self).__init__(temppath,prefix)
    self.__pbesfile = filename
    if name.startswith('pbesparelm'):
      self.__reducedPbesfile = self._newTempFilename('pbes', '.parelm.constelm')
      self.__besfile = self._newTempFilename('bes', '.parelm.constelm')
    elif name.startswith('pbesstategraph'):
      self.__reducedPbesfile = self._newTempFilename('pbes', '.stategraph.constelm')
      self.__besfile = self._newTempFilename('bes', '.stategraph.constelm')
    else:
      self.__reducedPbesfile = self.__pbesfile
      self.__besfile = self._newTempFilename('bes')
    self.name = name
    self.result = {}
    self.result['name'] = self.name
    self.result['times'] = {}
    self.result['times']['instantiation'] = 'unknown'
    self.result['times']['reduction'] = 'unknown'
    self.result['times']['solving'] = 'unknown'
    self.result['memory'] = {}
    self.result['sizes'] = 'unknown'
    self.result['solution'] = 'unknown'
  
  def __reduce(self, log):
    log.debug('Creating temp files')
    if self.name.startswith('pbesparelm'):
      tmpfile = self._newTempFilename('pbes', '.parelm')
    elif self.name.startswith('pbesstategraph'):
      tmpfile = self._newTempFilename('pbes', '.stategraph')
    else:
      return
    
    
    try:
      if self.name.startswith('pbesparelm'):
        log.debug('Parelm')
        result = tools.pbesparelm(self.__pbesfile, tmpfile, timed=True, timeout=REDUCTION_TIMEOUT, memlimit=MEMLIMIT)
      else:
        log.debug('Stategraph')
        result = tools.pbesstategraph(self.__pbesfile, tmpfile, timed=True, timeout=REDUCTION_TIMEOUT, memlimit=MEMLIMIT)
       
      self.result['times']['reduction'] = result['times']

      tools.pbesconstelm(tmpfile, self.__reducedPbesfile, timed=True)
    
    except (tools.Timeout) as e:
      log.info('Timeout (reducing)')
      self.result['times']['reduction'] = 'timeout'
      raise e   
    except (tools.OutOfMemory) as e:
      log.info('Out of memory (reducing)')
      self.result['memory']['reduction'] = 'outofmemory'
      raise e

    
  def __instantiate(self, log):
    try:
      result = tools.pbes2bes('-rjittyc', self.__reducedPbesfile, self.__besfile, timeout=GENERATE_TIMEOUT, memlimit=MEMLIMIT, timed=True)
      self.result['times']['instantiation'] = result['times']
      
      info = tools.besinfo(self.__besfile, '-v', memlimit=MEMLIMIT)['out']
      BESINFO_RE = '.*Number of equations:\s*(?P<eqns>\d+)' \
               '.*Number of mu.?s:\s*(?P<mueqns>\d+)' \
               '.*Number of nu.?s:\s*(?P<nueqns>\d+)' \
               '.*Block nesting depth:\s*(?P<bnd>\d+).*?'
      m = re.search(BESINFO_RE, info, re.DOTALL)
      self.result['sizes'] = m.groupdict()
      
    except (tools.Timeout) as e:
      log.info('Timeout (intantiating)')
      self.result['times']['instantiation'] = 'timeout'
      raise e
    except (tools.OutOfMemory) as e:
      log.info('Out of memory (instantiating)')
      self.result['memory']['instantiation'] = 'outofmemory'
      raise e
    
  def __solve(self, log):
    try:      
      result = tools.pbespgsolve(self.__besfile, timed=True, timeout=SOLVE_TIMEOUT, memlimit=MEMLIMIT)
      self.result['times']['solving'] = result['times']      
      self.result['solution'] = result['out'].strip()
    except (tools.Timeout):
      log.info('Timeout (solving)')
      self.result['times']['solving'] = 'timeout'
    except (tools.OutOfMemory):
      log.info('Out of memory (solving)')        
      self.result['memory']['solving'] = 'outofmemory'
  
  def phase0(self, log):
    try:
      log.info('Reducing PBES')
      self.__reduce(log)
      log.info('Instantiating PBES')
      self.__instantiate(log)
      log.info('Solving PBES')
      self.__solve(log)
    except:
      pass
  
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
    #tmp = tools.pbesrewr('-pquantifier-one-point', stdin=tmp['out'], memlimit=MEMLIMIT)
    #tmp = tools.pbesrewr('-psimplify', stdin=tmp['out'], memlimit=MEMLIMIT)
    tmp = tools.pbesconstelm(stdin=tmp['out'], memlimit=MEMLIMIT)

    log.debug("Writing PBES")
    pbes = open(self.__pbesfile, 'w')
    pbes.write(tmp['out'])
    pbes.close()
    
  def __reduce(self, pbesfile, log):
    log.debug('Reduction...')
    self.subtasks = [ 
      ReduceAndSolveTask('original', self._prefix, pbesfile, self._temppath),
      ReduceAndSolveTask('pbesparelm', self._prefix, pbesfile, self._temppath),
      ReduceAndSolveTask('pbesstategraph', self._prefix, pbesfile, self._temppath),
    ]
    
  def phase0(self, log):
    log.debug('Generating initial PBES')
    try:
      self._writePBESfile(log)
      log.debug('Reducing PBES and instantiating and solving')
      self.__reduce(self.__pbesfile, log)
    except tools.ToolException as e:
      log.warning('Failed to generate PBES for {0} with exception\n{1}'.format(self, e))
      self.result['original'] = 'failed'
    
  def phase1(self, log):
    for task in self.results:
      self.result[task.name] = task.result
    
