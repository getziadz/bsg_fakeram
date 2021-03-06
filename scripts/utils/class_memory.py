import math
import os

from utils.cacti_config import cacti_config

################################################################################
# MEMORY CLASS
#
# This class stores the infromation about a specific memory that is being
# generated. This class takes in a process object, the infromation in one of
# the items in the "sram" list section of the json configuration file, and
# finally runs cacti to generate the rest of the data.
################################################################################

class Memory:

  def __init__( self, process, sram_data ):

    self.process        = process
    self.name           = str(sram_data['name'])
    self.width_in_bits  = int(sram_data['width'])
    self.depth          = int(sram_data['depth'] )
    self.num_banks      = int(sram_data['banks'] )
    self.rw_ports       = 1
    self.width_in_bytes = math.ceil(self.width_in_bits / 8.0)
    self.total_size     = self.width_in_bytes * self.depth

    self.results_dir = os.sep.join([os.getcwd(), 'results', self.name])
    if not os.path.exists( self.results_dir ):
      os.makedirs( self.results_dir )

    self.__run_cacti()
    with open( os.sep.join([self.results_dir, 'cacti.cfg.out']), 'r' ) as fid:
      lines = [line for line in fid]
      cacti_data = lines[1].split(',')

    self.standby_leakage_per_bank_mW = float(cacti_data[11])
    self.access_time_ns              = float(cacti_data[5])
    self.cycle_time_ns               = float(cacti_data[6])
    self.dynamic_read_power_mW       = float(cacti_data[10])
    self.aspect_ratio                = float(cacti_data[31])
    self.area_um2                    = float(cacti_data[12])*1e6
    self.fo4_ps                      = float(cacti_data[30])
    self.cap_input_pf                = float(cacti_data[32])
    self.width_um                    = math.sqrt( self.area_um2 * self.aspect_ratio )
    self.height_um                   = math.sqrt( self.area_um2 / self.aspect_ratio )

    self.width_um = (math.ceil((self.width_um*1000.0)/self.process.snapWidth_nm)*self.process.snapWidth_nm)/1000.0
    self.height_um = (math.ceil((self.height_um*1000.0)/self.process.snapHeight_nm)*self.process.snapHeight_nm)/1000.0
    self.area_um2 = self.width_um * self.height_um

    self.pin_dynamic_power_mW        = (0.5 * self.cap_input_pf * (float(self.process.voltage)**2))*1e9 ;# P = 0.5*CV^2
    self.t_setup_ns                  = self.access_time_ns ;# access time is clk to Q, assume that data to "reg" is about the same.
    self.t_hold_ns                   = 0

  # __run_cacti: shell out to cacti to generate a csv file with more data
  # regarding this memory based on the input parameters from the json
  # configuration file.
  def __run_cacti( self ):
    fid = open(os.sep.join([self.results_dir,'cacti.cfg']), 'w')
    fid.write( '\n'.join(cacti_config).format( self.total_size
             , self.width_in_bytes, self.rw_ports, 0, 0
             , self.process.tech_um, self.width_in_bits, self.num_banks ))
    fid.close()
    odir = os.getcwd()
    os.chdir(os.environ['CACTI_BUILD_DIR'] )
    os.system( os.sep.join(['.','cacti -infile ']) + os.sep.join([self.results_dir,'cacti.cfg']))
    os.chdir(odir)

