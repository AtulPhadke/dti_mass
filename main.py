from brukerapi.dataset import Dataset
from dipy.io.image import load_nifti, save_nifti
from dipy.io import read_bvals_bvecs
from dipy.core.gradients import gradient_table
from dipy.reconst.dti import TensorModel
from dipy.segment.mask import median_otsu
import dipy.reconst.dti as dti
from dipy.core.histeq import histeq
import os
import re
import nibabel as nib
import numpy as np
import math
import inquirer as iq
import shutil

folder = "lsd_data"


def checkMethod(scan_set):
	f = open(os.path.join(scan_set, "method"))
	contents = f.read()
	if "Method=<Bruker:DtiEpi>" in contents:
		return True
	else:
		return False

def checkRare(scan_set):
	f = open(os.path.join(scan_set, "method"))
	contents = f.read()
	if "Method=<Bruker:RARE>" in contents:
		return True
	else:
		return False


dti_scans = {}
rare_scans = {}

class DTI:
	def __init__(self, DTI_FILE, NEW_NAME, OUTPUT_DIR):
		self.chosen_file = DTI_FILE
		self.new_name = NEW_NAME
		self.OUTPUT_DIR = OUTPUT_DIR

	def generate_bvals(self, file):
		#method_file = os.path.abspath(os.path.join(os.path.join(os.path.join(file, ".."), ".."), ".."))
		#method_file = os.path.join(method_file, "method")
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
					#if self.directions[("b"+str(f))]:
					dwDir.append(element.strip())

				dwDir = np.array(dwDir)
				dwDir.shape = (int(len(dwDir)/3),3)
				dwDir = dwDir.astype(float)
 
		bvec = np.dot(dwDir, GradOrient)
		bvec_file = open(os.path.join(self.OUTPUT_DIR, self.new_name+".bvec"), "w+")
		bval_file = open(os.path.join(self.OUTPUT_DIR, self.new_name+".bval"), "w+")

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

	def dti_fit(self, img):
		#img = Dataset(img).data
		fbval = os.path.join(self.OUTPUT_DIR, self.new_name+".bval")
		fbvec = os.path.join(self.OUTPUT_DIR, self.new_name+".bvec")

		bvals, bvecs = read_bvals_bvecs(fbval, fbvec)
		gtab = gradient_table(bvals, bvecs)
		tenmodel = TensorModel(gtab)

		fdata = np.array(img.get_fdata())

		tenfit = tenmodel.fit(fdata)

		return tenfit

def bruker2nifti(img):
	dataset = Dataset(img)
	return nib.Nifti1Image(dataset.data, None)

def getOnlyDirs(path):
	return [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]

def getVoxelSize(scan):
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

def getParameters():
	questions = [iq.Checkbox('Saves',
                    message="What files do you want to save?",
                    choices=['Anatomy', 
                    'Original Nifti', 'FA', 'ADC', 'b0'],
                    ),]
	answers = iq.prompt(questions)
	return answers["Saves"]

parameters = getParameters()

for scan_folder in getOnlyDirs(folder):
	scan_folder = os.path.join(folder, scan_folder)
	for number in getOnlyDirs(scan_folder):
		number = os.path.join(scan_folder, number)
		if os.path.basename(number) != "AdjResult":
			if checkMethod(number):
				if number in dti_scans:
					dti_scans[scan_folder] += [(str(number))]
				else:
					dti_scans[scan_folder] = [(str(number))]
			if checkRare(number):
				rare_scans[scan_folder] = number

bool_anatomy = False
bool_ognii = False
bool_fa = False
bool_adc = False
bool_b0 = False

if "Anatomy" in parameters:
	bool_anatomy = True
if "Original Nifti" in parameters:
	bool_ognii = True
if "FA" in parameters:
	bool_fa = True
if "ADC" in parameters:
	bool_adc = True
if "b0" in parameters:
	bool_b0 = True

if os.path.isdir("processed"):
	shutil.rmtree("processed")
os.mkdir("processed")

for scan, numb in dti_scans.items():
	if numb:
		if bool_fa or bool_adc or bool_b0:
			for number in numb:
				img_file = os.path.join(number, "pdata", "1", "2dseq")
				img = bruker2nifti(img_file)
				dim = getVoxelSize(number)
				method_file = os.path.join(number, "method")
				OUTPUT_DIR = os.path.join("processed", os.path.basename(scan))
				if not os.path.isdir(OUTPUT_DIR):
					os.mkdir(OUTPUT_DIR)
				diff = DTI(img, os.path.basename(scan), OUTPUT_DIR)
				diff.generate_bvals(method_file)
				tenfit = diff.dti_fit(img)
				if bool_b0:
					b0 = nib.Nifti1Image(img.get_fdata()[:,:,:,0], None)
					b0.header["pixdim"][1] = dim[0]
					b0.header["pixdim"][2] = dim[1]
					b0.header["pixdim"][3] = dim[2]
					nib.save(b0, os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_b0.nii"))
					print("Saved " + os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_b0.nii"))
				if bool_fa:
					fa = nib.Nifti1Image(tenfit.fa, None)
					fa.header["pixdim"][1] = dim[0]
					fa.header["pixdim"][2] = dim[1]
					fa.header["pixdim"][3] = dim[2]
					fa.header["pixdim"][4] = dim[3]
					nib.save(fa, os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_fa.nii"))
					print("Saved " + os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_fa.nii"))
				if bool_adc:
					md = nib.Nifti1Image(tenfit.md, None)
					md.header["pixdim"][1] = dim[0]
					md.header["pixdim"][2] = dim[1]
					md.header["pixdim"][3] = dim[2]
					md.header["pixdim"][4] = dim[3]
					nib.save(md, os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_adc.nii"))
					print("Saved " + os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_adc.nii"))
		if bool_ognii:
			for number in numb:
				OUTPUT_DIR = os.path.join("processed", os.path.basename(scan))
				img_file = os.path.join(number, "pdata", "1", "2dseq")
				if not os.path.isdir(OUTPUT_DIR):
					os.mkdir(OUTPUT_DIR)
				img = bruker2nifti(img_file)
				dim = getVoxelSize(number)
				img_nii = nib.Nifti1Image(img.get_fdata(), None)
				img_nii.header["pixdim"][1] = dim[0]
				img_nii.header["pixdim"][2] = dim[1]
				img_nii.header["pixdim"][3] = dim[2]
				img_nii.header["pixdim"][4] = dim[3]
				nib.save(img_nii, os.path.join(OUTPUT_DIR, os.path.basename(scan) +"_"+str(os.path.basename(number))+"_og.nii"))
			print("Saved " + str(os.path.join(OUTPUT_DIR, os.path.basename(scan) +"_"+str(os.path.basename(number))+"_og.nii")))
		if bool_anatomy:
			OUTPUT_DIR = os.path.join("processed", os.path.basename(scan))
			if not os.path.isdir(OUTPUT_DIR):
				os.mkdir(OUTPUT_DIR)
			number = rare_scans[scan]
			img_file = os.path.join(number, "pdata", "1", "2dseq")
			img = bruker2nifti(img_file)
			dim = getVoxelSize(number)
			img_anat = nib.Nifti1Image(img.get_fdata(), None)
			img_anat.header["pixdim"][1] = dim[0]
			img_anat.header["pixdim"][2] = dim[1]
			img_anat.header["pixdim"][3] = dim[2]
			nib.save(img_anat, os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_anat.nii"))
			print("Saved " + str(os.path.join(OUTPUT_DIR, os.path.basename(scan) +"_"+str(os.path.basename(number))+"_anat.nii")))



#print(dti_scans)
