import string
import os.path

class Spec(object):
  def __init__(self, template=None):
    self.TEMPLATE = template
    if self.TEMPLATE is None:
      self.TEMPLATE = self.__class__.TEMPLATE
  @property
  def _template(self):
    return string.Template(open(os.path.join(os.path.split(__file__)[0], 'mcrl2', self.TEMPLATE + '.mcrl2')).read())
  def mcrl2(self):
    return self._template.substitute()

class LiftSpec(Spec):
  def mcrl2(self, nlifts):
    return self._template.substitute(
      nlifts=nlifts,
      lifts=' || '.join(['Lift0({0})'.format(i + 1) for i in range(0, nlifts)]))

class LeaderSpec(Spec):
  def mcrl2(self, nparticipants):
    return self._template.substitute(nparticipants=nparticipants,
                                     parts=' || '.join(['Part({0})'.format (i+1) for i in range(0, nparticipants)]))

class DataSpec(Spec):
  def mcrl2(self, datasize):
    return self._template.substitute(
      data='|'.join(['d' + str(i + 1) for i in range(0, datasize)])
    )
    
class CCPSpec(Spec):
  '''Always assign all regions to each process, each thread tid is assigned to
     the process pid such that tid mod nprocesses == pid'''
  def mcrl2(self, nprocesses, nthreads, nregions):
    print "nprocesses: {0}, nthreads: {1}, nregions: {2}".format(nprocesses, nthreads, nregions)
    assert(nthreads >= nprocesses)
    assert(nregions > 0)
    
    processes = [' || '.join('''Locker(P{0}, 0, 0, 0, 0, 0, 0, 0, 0)
    || HomeQueue(P{0})
    || RemoteQueue(P{0})
    || Processor(P{0})
    '''.format(pid+1) for pid in range(0, nprocesses) )]
    regions = [' || '.join('''Region(P{0}, RGN(R{1}, P1, UNUSED, [], notnull, null, 0))'''.format(pid+1, rid+1) for rid in range(0, nregions) for pid in range(0, nprocesses))]
    threads = [' || '.join('''Thread(T{0}, P{1}, {{}})'''.format(tid+1, (tid % nprocesses)+1) for tid in range(0,nthreads))]
    
    return self._template.substitute(
      processids='|'.join(['P' + str(i+1) for i in range(0,nprocesses)]),
      threadids='|'.join(['T' + str(i+1) for i in range(0,nthreads)]),
      regionids='|'.join(['R' + str(i+1) for i in range(0,nregions)]),
      init=' || '.join(processes + regions + threads)
    )
    
class ElevatorSpec(Spec):
  def mcrl2(self, policy, storeys):
    return self._template.substitute(policy=policy, storeys=storeys)

class SWPSpec(Spec):
  TEMPLATE = 'swp'
  def mcrl2(self, windowsize, datasize):
    return self._template.substitute(
      windowsize=windowsize,
      data='|'.join(['d' + str(i + 1) for i in range(0, datasize)]),
      initialwindow='[{0}]'.format(','.join(['d1'] * windowsize)),
      emptywindow='[{0}]'.format(','.join(['false'] * windowsize))
    )
    
class HanoiSpec(Spec):
  TEMPLATE = 'hanoi'
  def mcrl2(self, ndisks):
    return self._template.substitute(ndisks=ndisks)
  
class IEEE1394Spec(Spec):
  TEMPLATE = 'ieee1394'
  def mcrl2(self, nparties, datasize, headersize, acksize):
    return self._template.substitute(
      nparties=nparties,
      data='|'.join(['d' + str(i + 1) for i in range(0, datasize)]),
      headers='|'.join(['h' + str(i + 1) for i in range(0, headersize)]),
      acks='|'.join(['a' + str(i + 1) for i in range(0, acksize)]),
      links=' || '.join(['LINK(N,{0})'.format(n) for n in range(0,nparties)])
    )

class BoardSpec(Spec):
  def __init__(self, template=None):
    super(BoardSpec,self).__init__(template)
  
  def mcrl2(self, width, height):
    return self._template.substitute(
      width=width,
      height=height
    )

class OthelloSpec(BoardSpec):
  def __init__(self, template=None):
    super(OthelloSpec,self).__init__(template)
  
  def mcrl2(self, width, height):
    assert(width % 2 == 0)
    assert(width >= 4)
    assert(height % 2 == 0)
    assert(height >= 4)
    
    return self._template.substitute(
      extrarows = int((height-2/2)),
      extracolumns = int((width-2/2))
    )

__SPECS = {
    'Debug spec': Spec('debugging'),
    'Lossy buffer': DataSpec('lossy_buffer'),
    'Smaller': DataSpec('smaller'),
    'Small': Spec('small'),
    'ABP':DataSpec('abp'),
    'ABP(BW)':DataSpec('abp_bw'),
    'CABP':DataSpec('cabp'),
    'Par':DataSpec('par'),
    'CCP':CCPSpec('ccp'),
    'Hesselink':DataSpec('hesselink'),
    'BRP':DataSpec('brp'),
    'SWP': SWPSpec(),
    'Onebit': DataSpec('onebit'),
    'IEEE1394': IEEE1394Spec(),
    'Lift (Incorrect)': LiftSpec('lift-incorrect'),
    'Lift (Correct)': LiftSpec('lift-correct'),
    'Hanoi': HanoiSpec('hanoi'),
    'Elevator': ElevatorSpec('elevator'),
    'Leader': LeaderSpec('leader'),
    'Snake': BoardSpec('snake'),
    'Clobber': BoardSpec('clobber'),
    'Hex': BoardSpec('hex'),
    'Domineering': BoardSpec('domineering'),
    'Othello': OthelloSpec('othello')
  }

def get(name):
  return __SPECS[name]
