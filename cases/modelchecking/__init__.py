from cases import tools, TempObj, PBESCase, MEMLIMIT
import specs
import os.path
import logging
import tempfile
import re
import sys
import multiprocessing
import traceback

class Property(PBESCase):
  def __init__(self, description, lps, mcf, temppath):
    PBESCase.__init__(self, temppath=temppath, prefix=description + '_' + os.path.splitext(os.path.split(mcf)[1])[0])
    self.__desc = description
    self.__detailed_desc = description + '_' + os.path.splitext(os.path.split(mcf)[1])[0]
    self._temppath = temppath
    self.lps = lps
    self.mcffile = mcf
    self.renfile = os.path.splitext(self.mcffile)[0] + '.ren'
  
  def __str__(self):
    return os.path.splitext(os.path.split(self.mcffile)[1])[0]
  
  def __rename(self):
    '''If a lpsactionrename specification exists for this property, transform
       the LPS.'''
    if os.path.exists(self.renfile):
      self.lps = tools.lpsactionrename('-f', self.renfile, '-v', stdin=self.lps, memlimit=MEMLIMIT)['out']
  
  def _makePBES(self):
    '''Generate a PBES out of self.lps and self.mcffile, and apply pbesconstelm
       to it.'''
    self.__rename()
    return tools.lps2pbes('-f', self.mcffile, '-v', stdin=self.lps, memlimit=MEMLIMIT)['out']

class Case(TempObj):
  def __init__(self, name, **kwargs):
    TempObj.__init__(self)
    spec = specs.get(name)
    self.__name = name
    self.__kwargs = kwargs
    self._mcrl2 = spec.mcrl2(**kwargs)
    self._temppath = os.path.join(os.path.split(__file__)[0], 'temp')
    self._prefix = '{0}{1}'.format(self.__name, ('_'.join('{0}={1}'.format(k,v) for k,v in self.__kwargs.items())))
    self.proppath = os.path.join(os.path.split(__file__)[0], 'properties', spec.TEMPLATE)
    self.result = {}
  
  def __str__(self):
    argstr = ', '.join(['{0}={1}'.format(k, v) for k, v in self.__kwargs.items()])
    return '{0}{1}'.format(self.__name, ' [{0}]'.format(argstr) if argstr else '')

  def _makeLPS(self, log):
    '''Linearises the specification in self._mcrl2.'''
    log.debug('Linearising {0}'.format(self))
    return tools.mcrl22lps('-nf', stdin=self._mcrl2, memlimit=MEMLIMIT)['out']

  def phase0(self, log):
    '''Generates an LPS and creates subtasks for every property that should be
    verified.'''
    try:
      lps = self._makeLPS(log)    
      for prop in os.listdir(self.proppath):
        if not prop.endswith('.mcf'):
          continue
        self.subtasks.append(Property(self._prefix, lps, os.path.join(self.proppath, prop), 
                                      self._temppath))
    except (tools.ToolException, tools.Timeout, tools.OutOfMemory) as e:
      log.error('Failed to generate LPS for {0} with exception\n{1}'.format(self, e))
      self.result['original'] = 'failed'      
    
  def phase1(self, log):
    log.debug('Finalising {0}'.format(self))
    for prop in self.results:
      self.result[str(prop)] = prop.result

class GameCase(Case):
  def __init__(self, name, use_compiled_constelm=False, **kwargs):
    super(GameCase, self).__init__(name, **kwargs)
    self.__boardwidth = kwargs.get('width')
    self.__boardheight = kwargs.get('height')
    self.__use_compiled_constelm = use_compiled_constelm
    
  def _makeLPS(self, log):
    '''Linearises the specification in self._mcrl2 and applies lpssuminst,
    lpsparunfold and lpsconstelm to the result.'''
    log.debug('Linearising {0}'.format(self))
    result = tools.mcrl22lps('-vnf', stdin=self._mcrl2, memlimit=MEMLIMIT)
    log.debug('Applying suminst on LPS of {0}'.format(self))
    result = tools.lpssuminst(stdin=result['out'], memlimit=MEMLIMIT)
    log.debug('Applying parunfold (for Board) on LPS of {0}'.format(self))
    result = tools.lpsparunfold('-lv', '-n{0}'.format(self.__boardheight), '-sBoard', stdin=result['out'], memlimit=MEMLIMIT)
    log.debug('Applying parunfold (for Row) on LPS of {0}'.format(self))
    result = tools.lpsparunfold('-lv', '-n{0}'.format(self.__boardwidth), '-sRow', stdin=result['out'], memlimit=MEMLIMIT)
    log.debug('Applying constelm on LPS of {0}'.format(self))
    result = tools.lpsconstelm('-ctvrjittyc' if self.__use_compiled_constelm else '-ctv', stdin=result['out'], memlimit=MEMLIMIT)
    return result['out']

def getcases(debug):
  if debug:
    return [Case('Debug spec'),
     Case('Lossy buffer', datasize=8)]
  else:
    return \
      [Case('Debug spec')] + \
      [Case('Lossy buffer', datasize=i) for i in [2,3,4,5,6,7,8,16,32,64,128]] + \
      [Case('ABP', datasize=i) for i in [2,4,8,16,32]] + \
      [Case('Hesselink', datasize=i) for i in range(2,5)] + \
      [Case('SWP', windowsize=1, datasize=i) for i in range(2, 7)] + \
      [Case('SWP', windowsize=2, datasize=i) for i in range(2, 7)] + \
      [Case('BRP', datasize=i) for i in [3]] + \
      [Case('Elevator', policy=p, storeys=n) for p in ['FIFO', 'LIFO'] for n in range(3,6)] + \
      [GameCase('Othello', width=4, height=4)] + \
      [GameCase('Clobber', width=4, height=4)] + \
      [GameCase('Snake', width=4, height=4)] + \
      [GameCase('Hex', width=4, height=4)] + \
      [GameCase('Domineering', width=4, height=4)] + \
      [Case('IEEE1394', nparties=n, datasize=2, headersize=2, acksize=2) for n in range(2,5)] + \
      [Case('Hanoi', ndisks=n) for n in range(10,18)] + \
      [Case('Lift (Correct)', nlifts=n) for n in range(2, 5)] + \
      [Case('Lift (Incorrect)', nlifts=n) for n in range(2, 5)] + \
      [Case('SWP', windowsize=3, datasize=i) for i in range(2, 5)] + \
      [Case('SWP', windowsize=4, datasize=2)] + \
      [Case('Onebit', datasize=i) for i in range(2,5)] + \
      [Case('Leader', nparticipants=n) for n in range(3, 7)]
