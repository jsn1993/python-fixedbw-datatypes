#=========================================================================
# Bits.py
#=========================================================================

import copy

__cache__ = {}

#-------------------------------------------------------------------------
# Bits
#-------------------------------------------------------------------------
def Bits( nbits ):
  '''A metaclass constructor for creating Bits objects.

  To construct a new Bits object, intantiate like:

    Bits( nbits=4 )( value=5 )
  '''

  # convert Bits objects into integer
  nbits = int(nbits)

  try:
    return __cache__[ nbits ]
  except KeyError:
    new_class = type( 'Bits{}'.format( nbits ),  # class name
                      (BitsN,),                  # base class
                                                 # class dictionary
                      {'nbits'  : nbits,
                       '_max'   : (2**nbits) - 1,
                       '_min'   : -2**(nbits - 1) if nbits > 1 else 0,
                       '_mask'  : (1 << nbits) - 1,
                       '_hchars': ((nbits - 1) / 4) + 1,
                       '_ochars': ((nbits - 1) / 2) + 1,
                      } )
    __cache__[ nbits ] = new_class
    return new_class

#-------------------------------------------------------------------------
# BitsN
#-------------------------------------------------------------------------
class BitsN( object ):
  'Base class for templated Bits objects.'

  #-----------------------------------------------------------------------
  # __init__
  #-----------------------------------------------------------------------
  def __init__( self, value = 0, trunc = False ):

    # convert Bits objects into integer

    value = int( value )

    if not trunc:
      assert self._min <= value <= self._max

    # Convert negative values into unsigned ints and store them

    value_uint = value if ( value >= 0 ) else ( ~(-value) + 1 )
    self._uint = value_uint & self._mask

  #-----------------------------------------------------------------------
  # __int__
  #-----------------------------------------------------------------------
  def __int__( self ):
    'Type conversion to an int.'
    return int( self._uint )

  #-----------------------------------------------------------------------
  # __long__
  #-----------------------------------------------------------------------
  def __long__( self ):
    'Type conversion to a long.'
    return long( self._uint )

  #-----------------------------------------------------------------------
  # __index__
  #-----------------------------------------------------------------------
  def __index__( self ):
    'Behave like an int() when used as an index to slices.'
    return self._uint

  #-----------------------------------------------------------------------
  # uint
  #-----------------------------------------------------------------------
  def uint( self ):
    'Return the unsigned integer representation of the bits.'
    return self._uint

  #-----------------------------------------------------------------------
  # int
  #-----------------------------------------------------------------------
  def int( self ):
    'Return the integer representation of the bits.'
    if self[ self.nbits - 1]:
      twos_complement = ~self + 1
      return -twos_complement._uint
    else:
      return self._uint

  #-----------------------------------------------------------------------
  # bit_length
  #-----------------------------------------------------------------------
  def bit_length( self ):
    '''Implement bit_length method provided by the int built-in.
    (Simplifies the implementation of get_nbits()).'''
    return self._uint.bit_length()

  #-----------------------------------------------------------------------
  # print methods
  #-----------------------------------------------------------------------

  def __repr__(self):
    return "Bits( {0}, {1} )".format(self.nbits, self.hex())

  def __str__(self):
    str = "{:x}".format(self._uint).zfill( self._hchars )
    return str

  def __oct__( self ):
    print "DEPRECATED: Please use .oct()!"
    return self.oct()

  def __hex__( self ):
    print "DEPRECATED: Please use .oct()!"
    return self.hex()

  def bin(self):
    str = "{:b}".format(self._uint).zfill(self.nbits)
    return "0b"+str

  def oct( self ):
    str = "{:o}".format(self._uint).zfill( self._ochars )
    return "0o"+str

  def hex( self ):
    str = "{:x}".format(self._uint).zfill( self._hchars )
    return "0x"+str

  #------------------------------------------------------------------------
  # __getitem__
  #------------------------------------------------------------------------
  def __getitem__( self, addr ):
    'Read a subset of bits using slice notation.'

    # TODO: optimize this logic?

    # Handle slices
    if isinstance( addr, slice ):

      # Parse address range
      start = addr.start
      stop  = addr.stop

      # Open-ended range ( [:] ), return a copy of self
      if start is None and stop is None:
        return copy.copy( self )

      # Open-ended range on left ( [:N] )
      elif start is None:
        start = 0

      # Open-ended range on right ( [N:] )
      elif stop is None:
        stop = self.nbits

      stop  = int( stop  )
      start = int( start )

      # Verify our ranges are sane
      if not (start < stop):
        raise IndexError('Start index is not less than stop index')
      if not (0 <= start < stop <= self.nbits):
        raise IndexError('Bits index out of range')

      # Create a new Bits object containing the slice value and return it
      nbits = stop - start
      mask  = (1 << nbits) - 1
      value = (self._uint & (mask << start)) >> start
      return Bits(nbits)(value)

    # Handle integers
    else:

      addr = int(addr)

      # Verify the index is sane
      if not (0 <= addr < self.nbits):
        raise IndexError('Bits index out of range')

      # Create a new Bits object containing the bit value and return it
      value = (self._uint & (1 << addr)) >> addr
      return Bits(1)(value)

  #------------------------------------------------------------------------
  # __setitem__
  #------------------------------------------------------------------------
  def __setitem__( self, addr, value ):
    'Write a subset of bits using slice notation.'

    # TODO: optimize this logic?

    value = int( value )

    # Handle slices
    if isinstance( addr, slice ):

      # Parse address range
      start = addr.start
      stop  = addr.stop

      # Open-ended range ( [:] )
      if start is None and stop is None:
        assert self._min <= value <= self._max
        self._uint = value
        return

      # Open-ended range on left ( [:N] )
      elif start is None:
        start = 0

      # Open-ended range on right ( [N:] )
      elif stop is None:
        stop = self.nbits

      # Verify our ranges are sane
      if not (0 <= start < stop <= self.nbits):
        raise IndexError('Bits index out of range')

      nbits = stop - start

      # This assert fires if the value you are trying to store is wider
      # than the bitwidth of the slice you are writing to!
      assert nbits >= _get_nbits( value )

      # Clear the bits we want to set
      ones  = (1 << nbits) - 1
      mask = ~(ones << start)
      cleared_val = self._uint & mask

      # Set the bits, anding with ones to ensure negative value assign
      # works that way you would expect.
      self._uint = cleared_val | ((value & ones) << start)

    # Handle integers
    else:

      # Verify the index and values are sane
      if not (0 <= addr < self.nbits):
        raise IndexError('Bits index out of range')
      assert 0 <= value <= 1

      # Clear the bits we want to set
      mask = ~(1 << addr)
      cleared_val = self._uint & mask

      # Set the bits
      self._uint = cleared_val | (value << addr)

  #------------------------------------------------------------------------
  # arithmetic operators
  #------------------------------------------------------------------------
  # For now, let's make the width equal to the max of the widths of the
  # two operands. These semantics match Verilog:
  #
  #   http://www1.pldworld.com/@xilinx/html/technote/TOOL/MANUAL/21i_doc/data/fndtn/ver/ver4_4.htm

  def __invert__( self ):
    return Bits(self.nbits)( ~self._uint, trunc=True )

  def __add__( self, other ):
    try:    return Bits(max(self.nbits, other.nbits))( self._uint + other._uint, trunc=True)
    except: return Bits(self.nbits                  )( self._uint + other,       trunc=True)

  def __sub__( self, other ):
    try:    return Bits(max(self.nbits, other.nbits))( self._uint - other._uint, trunc=True)
    except: return Bits(self.nbits                  )( self._uint - other,       trunc=True)

  def __mul__( self, other ):
    try:    return Bits(2*max(self.nbits, other.nbits))( self._uint * other._uint, trunc=True)
    except: return Bits(2*self.nbits                  )( self._uint * other,       trunc=True)

  def __radd__( self, other ):
    return self.__add__( other )

  def __rsub__( self, other ):
    return Bits(_get_nbits( other ))( other ) - self

  def __rmul__( self, other ):
    return self.__mul__( other )

  def __div__(self, other):
    try:    return Bits(2*max(self.nbits, other.nbits))( self._uint / other._uint, trunc=True )
    except: return Bits(2*self.nbits                  )( self._uint / other,       trunc=True )

  def __floordiv__(self, other):
    try:    return Bits(2*max(self.nbits, other.nbits))( self._uint / other._uint, trunc=True )
    except: return Bits(2*self.nbits                  )( self._uint / other,       trunc=True )

  def __mod__(self, other):
    try:    return Bits(2*max(self.nbits, other.nbits))( self._uint % other._uint, trunc=True )
    except: return Bits(2*self.nbits                  )( self._uint % other,       trunc=True )

  def __divmod__(self, other):
    raise NotImplementedError()

  def __pow__(self, other):
    raise NotImplementedError()


  #------------------------------------------------------------------------
  # shift operators
  #------------------------------------------------------------------------

  def __lshift__( self, other ):
    # Optimization to return 0 if shift amount is greater than self.nbits
    if int( other ) >= self.nbits: return Bits( self.nbits )( 0 )
    return Bits( self.nbits )( self._uint << int( other ), trunc=True )

  def __rshift__( self, other ):
    return Bits( self.nbits )( self._uint >> int( other ) )

  # TODO: Not implementing reflective operators because its not clear
  #       how to determine width of other object in case of lshift
  #def __rlshift__(self, other):
  #  return self.__lshift__( other )
  #def __rrshift__(self, other):
  #  return self.__rshift__( other )

  #------------------------------------------------------------------------
  # Bitwise Operators
  #------------------------------------------------------------------------

  def __and__( self, other ):
    assert other >= 0
    try:    return Bits(max(self.nbits, other.nbits))( self._uint & other._uint, trunc=True )
    except: return Bits(self.nbits                  )( self._uint & other,       trunc=True )

  def __xor__( self, other ):
    assert other >= 0
    try:    return Bits(max( self.nbits, other.nbits))( self._uint ^ other._uint, trunc=True )
    except: return Bits(self.nbits                   )( self._uint ^ other,       trunc=True )

  def __or__( self, other ):
    assert other >= 0
    try:    return Bits(max( self.nbits, other.nbits))( self._uint | other._uint, trunc=True )
    except: return Bits(self.nbits                   )( self._uint | other,       trunc=True )

  def __rand__( self, other ):
    return self.__and__( other )

  def __rxor__( self, other ):
    return self.__xor__( other )

  def __ror__( self, other ):
    return self.__or__( other )

  #------------------------------------------------------------------------
  # comparison operators
  #------------------------------------------------------------------------
  # TODO: allow comparison with negative numbers?
  # TODO: should we return Bits(1) or boolean?

  def __nonzero__( self ):
    return self._uint != 0

  def __eq__( self, other ):
    if other is None: return False
    assert other >= 0
    return Bits(1)(self._uint == other)

  def __ne__( self, other ):
    if other is None: return True
    assert other >= 0
    return Bits(1)(self._uint != other)

  def __lt__( self, other ):
    assert other >= 0
    return Bits(1)(self._uint <  other)

  def __le__( self, other ):
    assert other >= 0
    return Bits(1)(self._uint <= other)

  def __gt__( self, other ):
    assert other >= 0
    return Bits(1)(self._uint >  other)

  def __ge__( self, other ):
    assert other >= 0
    return Bits(1)(self._uint >= other)

  #------------------------------------------------------------------------
  # zero/sign extension
  #------------------------------------------------------------------------

  def _zext( self, new_width ):
    'Zero extension'
    return Bits(new_width)(self._uint)

  def _sext( self, new_width ):
    'Sign extension'
    return Bits(new_width)(self.int())


#-------------------------------------------------------------------------
# _get_nbits
#-------------------------------------------------------------------------
# Return the number of bits needed to represent a value 'N'.
def _get_nbits( N ):
  if N > 0:
    return N.bit_length()
  else:
    return N.bit_length() + 1
