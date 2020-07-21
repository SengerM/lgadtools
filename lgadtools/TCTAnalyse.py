import ROOT as root
from .LGADSignal import LGADSignal

root.gSystem.Load('~/.TCTAnalyse.V2.2/TCTAnalyse.sl') # WARNING: this is hardcoded!

class PSTCT:
	# Experimental wrapper for the PSTCT class described here: http://particulars.si/TCTAnalyse/PSTCT.html#PSTCT:PSTCT
	def __init__(self, fname, time0 = 0, Bin = 2):
		self.root_object = root.PSTCT(fname, time0, Bin)
	
	def GetWF(self, ch=0, x=0, y=0, z=0, u1=0, u2=0):
		# Returns an LGADSignal object.
		# Arguments follow the same structure as "GetHA" described in particulars.si/TCTAnalyse/TCTAnalyse-UserGuide.html
		if type(ch) != type(x) != type(y) != type(z) != type(u1) != type(u2) != int:
			raise TypeError('All arguments must be int numbers')
		N_samples = self.root_object.GetHA(ch,x,y,z,u1,u2).GetNbinsX()
		time = [self.root_object.GetHA(ch,x,y,z,u1,u2).GetBinCenter(i) for i in range(N_samples)]
		samples = [self.root_object.GetHA(ch,x,y,z,u1,u2).GetBinContent(i) for i in range(N_samples)]
		return LGADSignal(time, samples)
	
	@property
	def Nx(self):
		# Number of "x" steps
		return self.root_object.Nx
	
	@property
	def Ny(self):
		# Number of "y" steps
		return self.root_object.Ny
	
	@property
	def Nz(self):
		# Number of "z" steps
		return self.root_object.Nz
	
	@property
	def dt(self):
		return self.root_object.dt
	
	@property
	def dx(self):
		# Size of one "x" step in meters
		return self.root_object.dx*2e-6
		
	@property
	def dy(self):
		# Size of one "y" step in meters
		return self.root_object.dy*2e-6

	@property
	def dz(self):
		# Size of one "z" step in meters
		return self.root_object.dz*2e-6
	
	@property
	def x0(self):
		return self.root_object.x0*2e-6
	
	@property
	def y0(self):
		return self.root_object.y0*2e-6
	
	@property
	def z0(self):
		return self.root_object.z0*2e-6
