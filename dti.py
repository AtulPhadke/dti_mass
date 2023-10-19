import os
import nibabel as nib
from dipy.io.image import load_nifti, save_nifti
from dipy.io import read_bvals_bvecs
from dipy.core.gradients import gradient_table
from dipy.reconst.dti import TensorModel
from dipy.segment.mask import median_otsu
import dipy.reconst.dti as dti
from dipy.core.histeq import histeq
from brukerapi.dataset import Dataset
import math
import numpy as np

class DTI:
	def __init__(self, DTI_FOLDER):
		self.DTI_FOLDER = DTI_FOLDER
		self.output_folder = ""
		self.dti_scans, self.dti_imgs, self.rare_scans, self.rare_imgs = self.filter_scans()

	def generate_bvals(self, file, OUTPUT_FOLDER, new_name, directions):
		f=open(file)
		no_line_breaks = f.read()
		content = no_line_breaks.split("\n")

		bval = None
		dwDir = None
		GradOrient = None

		for line in content:
			if "PVM_DwBvalEach" in line and not bval:
				bval = content[content.index(line)+1]

			elif "PVM_SPackArrGradOrient" in line and not GradOrient:

				reshape = line.replace("##$PVM_SPackArrGradOrient=( ", "")
				reshape = reshape.replace(" )", "").replace(",", "")
				reshape = list(reshape.split(" "))
				reshape = tuple([int(item) for item in reshape])

				vals = np.prod(list(reshape))

				GradOrientArray = content[content.index(line)+1:content.index(line)+4]
				GradOrient = []

				for c in GradOrientArray:
					d = c.split(" ")
					for grd in d:
						GradOrient.append(grd)

				GradOrient = np.array(list(filter(None, GradOrient)))
				GradOrient = GradOrient[0:vals]
				GradOrient.shape = reshape
				GradOrient = np.squeeze(GradOrient)
				GradOrient = GradOrient.astype(float)

			elif "##$PVM_DwDir=" in line and not dwDir:

				dwDirArray = no_line_breaks[no_line_breaks.index(content[content.index(line)+1]):no_line_breaks.find("#", no_line_breaks.index(content[content.index(line)+2]))].split(" ")
				dwDir = [0,0,0]

				for idx, element in enumerate(dwDirArray):
					f = math.floor(idx/3) + 1
					if directions[("b"+str(f))]:
						dwDir.append(element.strip())

				dwDir = np.array(dwDir)
				dwDir.shape = (int(len(dwDir)/3),3)
				dwDir = dwDir.astype(float)
 
		bvec = np.dot(dwDir, GradOrient)
		bvec_file = open(os.path.join(OUTPUT_FOLDER, new_name+".bvec"), "w+")
		bval_file = open(os.path.join(OUTPUT_FOLDER, new_name+".bval"), "w+")

		bval_file.truncate()

		#numb = sum(value == True for value in self.directions.values())

		bval_file.write("0 " + (len(dwDir)-1)*(str(bval) + " "))
		bval_file.close()

		bvec_file.truncate()

		bvec.shape = (len(dwDir), 3)

		for vector_array in bvec:
			for vector in vector_array:
				bvec_file.write(str(vector) + " ")
			bvec_file.write("\n")

		bvec_file.close()

	def dti_fit(self, OUTPUT_FOLDER, img, new_name):
		fbval = os.path.join(OUTPUT_FOLDER, new_name+".bval")
		fbvec = os.path.join(OUTPUT_FOLDER, new_name+".bvec")

		bvals, bvecs = read_bvals_bvecs(fbval, fbvec)
		gtab = gradient_table(bvals, bvecs)
		tenmodel = TensorModel(gtab)

		fdata = np.array(img.get_fdata())

		tenfit = tenmodel.fit(fdata)

		return tenfit

	def bruker2nifti(self,img):
		dataset = Dataset(img)
		return nib.Nifti1Image(dataset.data, None)

	def getOnlyDirs(self,path):
		return [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]

	def getVoxelSize(self,scan):
		method = open(os.path.join(scan, "method"))
		no_line_breaks = method.read()
		content = no_line_breaks.split("\n")
		foundSpat = False
		foundSlice = False
		sliceThickness = ""
		for line in content:
			if "PVM_SpatResol=" in line:
				foundSpat = True
				continue
			if foundSpat:
				foundSpat = False
				foundSlice = True
				spatial = line.split(" ")
				#print(spatial)
				continue
			if foundSlice:
				sliceThickness = line.replace("##$PVM_SliceThick=", "")
				#print(sliceThickness)
				foundSlice = False

		spatial.append(sliceThickness)

		return list(map(float, spatial))

	def checkMethod(self,scan_set):
		method_file = os.path.join(scan_set, "method")
		if os.path.exists(method_file):
			f = open(method_file)
			contents = f.read()
			if "Method=<Bruker:DtiEpi>" in contents:
				return True
			else:
				return False

	def checkRare(self,scan_set):
		method_file = os.path.join(scan_set, "method")
		if os.path.exists(method_file):
			f = open(method_file)
			contents = f.read()
			if "Method=<Bruker:RARE>" in contents:
				return True
			else:
				return False

	def filter_scans(self):
		dti_scans = {}
		dti_imgs = {}
		rare_scans = {}
		rare_imgs = {}

		for scan_folder in self.getOnlyDirs(self.DTI_FOLDER):
			scan_folder = os.path.join(self.DTI_FOLDER, scan_folder)
			for number in self.getOnlyDirs(scan_folder):
				number = os.path.join(scan_folder, number)
				if os.path.basename(number) != "AdjResult":
					if self.checkMethod(number):
						if number in dti_scans:
							dti_scans[scan_folder] += [(str(number))]
							dti_imgs[scan_folder] += [(self.bruker2nifti(os.path.join(number, "pdata", "1", "2dseq")))]
						else:
							dti_scans[scan_folder] = [(str(number))]
							dti_imgs[scan_folder] = [(self.bruker2nifti(os.path.join(number, "pdata", "1", "2dseq")))]
					if self.checkRare(number):
						rare_scans[scan_folder] = number
						rare_imgs[scan_folder] = self.bruker2nifti(os.path.join(number, "pdata", "1", "2dseq"))

		return dti_scans, dti_imgs, rare_scans, rare_imgs
