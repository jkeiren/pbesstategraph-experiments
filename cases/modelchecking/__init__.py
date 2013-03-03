from cases import tools, TempObj, PBESCase
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
    PBESCase.__init__(self)
    self.__desc = description
    self._temppath = temppath
    self._prefix = self.__desc + '_' + os.path.splitext(os.path.split(mcf)[1])[0]
    self.lps = lps
    self.mcffile = mcf
    self.renfile = os.path.splitext(self.mcffile)[0] + '.ren'
  
  def __str__(self):
    return os.path.splitext(os.path.split(self.mcffile)[1])[0]
  
  def __rename(self):
    '''If a lpsactionrename specification exists for this property, transform
       the LPS.'''
    if os.path.exists(self.renfile):
      self.lps = tools.lpsactionrename('-f', self.renfile, '-v', stdin=self.lps)
  
  def _makePBES(self):
    '''Generate a PBES out of self.lps and self.mcffile, and apply pbesconstelm
       to it.'''
    self.__rename()
    return tools.lps2pbes('-f', self.mcffile, '-v', stdin=self.lps)

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
    self.sizes = {}
    self.times = {}
    self.solutions = {}
    self.results = []
  
  def __str__(self):
    argstr = ', '.join(['{0}={1}'.format(k, v) for k, v in self.__kwargs.items()])
    return '{0}{1}'.format(self.__name, ' [{0}]'.format(argstr) if argstr else '')

  def _makeLPS(self, log):
    '''Linearises the specification in self._mcrl2.'''
    log.debug('Linearising {0}'.format(self))
    return tools.mcrl22lps('-nfv', stdin=self._mcrl2)

  def phase0(self, log):
    '''Generates an LPS and creates subtasks for every property that should be
    verified.'''
    lps = self._makeLPS(log)    
    for prop in os.listdir(self.proppath):
      if not prop.endswith('.mcf'):
        continue
      self.subtasks.append(Property(self._prefix, lps, os.path.join(self.proppath, prop), 
                                    self._temppath))
    
  def phase1(self, log):
    log.debug('Finalising {0}'.format(self))
    for prop in self.results:
      self.sizes[str(prop)] = prop.sizes
      self.times[str(prop)] = prop.times
      self.solutions[str(prop)] = prop.solutions

def getcases():
  return \
    [Case('Debug spec'),
     Case('Small')] +\
    [Case('Smaller', datasize=i) for i in [2,4,8,16,32]] + \
    [Case('ABP', datasize=i) for i in [2,4,8,16,32]] + \
    [Case('Hesselink', datasize=i) for i in [2]] + \
    [Case('SWP', windowsize=1, datasize=i) for i in range(2, 7)] + \
    [Case('SWP', windowsize=2, datasize=i) for i in range(2, 7)] + \
    [Case('BRP', datasize=i) for i in [3]] + \
    [Case('Othello'),
     Case('Clobber'),
     Case('Snake'),
     Case('Hex'),
     Case('Domineering'),
     Case('Elevator'),
     Case('Hanoi'),
     Case('IEEE1394')] + \
    [Case('Lift (Correct)', nlifts=n) for n in range(2, 5)] + \
    [Case('Lift (Incorrect)', nlifts=n) for n in range(2, 5)] + \
    [Case('SWP', windowsize=3, datasize=i) for i in range(2, 5)] + \
    [Case('SWP', windowsize=4, datasize=2)] + \
    [Case('Onebit', datasize=i) for i in range(2,5)] + \
    [Case('Leader', nparticipants=n) for n in range(3, 7)]
