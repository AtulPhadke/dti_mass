print("Loading")
import os
import nibabel as nib
import numpy as np
import math
import inquirer as iq
import shutil
from brukerapi.dataset import Dataset
from tkinter import filedialog
from dti import DTI
from visual import qualityChecker
import subprocess
import warnings
import matplotlib.pyplot as plt
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from uuid import getnode as get_mac
import sys

print("Checking License")
warnings.filterwarnings("ignore")

cred = credentials.Certificate({
  "type": "service_account",
  "project_id": "dwi-license",
  "private_key_id": "6c6c9e3f2d4629b5604c8abcc59db528534e5788",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDeHIC0gFc/slXK\nJYSRBpy3WwnRHJAtkiHaFvFNpC4QxVgG7OgWxVRue/1fne23Vq3uUWboFMAWlltD\nu4WAQ5JaR+e9I4Wsa4kaP0evfFjuPDCYuHYyvDECHNWg8AeZBKdEdx6KrzWg6is6\n2ly04+kYjHcHYWvNv/1rPvs2M+PS5IC980R3D5BufNNFNt7v7CGZuXLkD/XYexp0\nggCHuAFk61PpcTMmP+IYm6/xOiE7lIviWg6zw6pdBV2c64haZRMwYcgExEmYVfUR\nGP3/qpMqzyTpLPP+Mb4aXKx82MS5maQljc7UQgAV8+yjMARGEs+SAJlJNNtxMJjw\nMP08/8YFAgMBAAECggEADd6wyNTE3gToZ42tOBM2IRsNw2GpvTbFZ2WMXwFUIRb5\ntsD/g0CCU73pZhmqGQtQJDQwHWkCT8bG3zVsEkTl9D5OQdjghZJXhuyRsOsucH4Q\nuNC4DNYEp3Geg4TJrKwGN/fKT/W9/xTwayXsqR0cVryayDq0rS4CiLpvnIRkAyzE\n5vFucsfUg3YzGEdTm8kKFolCV7aXzRh9i8Ial4wBkoz1z/zedfWFX1K2kIb81Ynq\ndxphJIRhMFaqBTCkz8K/yPfRwZRBi3K8WpjF1giQUqxGvF8Rgy0UUamPoFYFGFeK\nDwBQKs+z3dz6587dxJiWVEyGs3dHKydXyZBog9yOpwKBgQD+mv8O2yyJLM0+nooC\nspV1pZzvEYXheljbSghhCv9ZCejcSZ4lrk4a95AUaYv0qyhmvxHtSJySsn5eV/4p\nkudRviHvFwy1tB1ovx68BV9TrVWcW8uWOkbeEWTiFcwM4v30UYHWUFjuTLLwlyLI\nJUXxKzH5TjOFBI/L5LCsUm1cVwKBgQDfU/GWxb+61Ew+BBKMSg8WUiuJDB+03jma\nAl5z8Mh55/DF8coUVDI/7fcQ1X5cUnKWe8X5A/gqGxH37aengO1ZH/Qsya+AJKIm\nlmcy4heOevdli1wOdqiBmHEYUb23qMeDAZf8csdnkvePr7yxSwhsn71kNg6XK+J0\nWZZEc4c3AwKBgFRpTua+A6X3FJUOOvNqAeNfZQhd5uU6ivspMF38J2x9vJZMUgJs\nJ7kJGtupop0boelur6Lb0A1S4FKnGbzu14JiZx29ppkXfiicNLRhk5lKfne4d2b3\nK0e0vJ24XE5pc4js/P7w5IsdIrZhZUa2FNpAV/Ev3CTdvk77Ixf+vANBAoGBAJjn\nuYZYeJBrYJQpZ6Wj4zaOJf6cTW0hpeCbdJ3/ItPMiR6OEKTgjNMWk81zzyNY09nS\nftai8BusEx5kGiDmdhtKdHzhzgZ3jonK+ndtM2G7MX3V7757YZ3xiKV0+ecwaQF6\natxOndZ9WoCHezMMQ4VTzXE6Tb0VL+QnnmnZi5+PAoGBAL5Fv8FrDpZ+5f4+l0ug\nHoWelE24IvXNx1o5CuKc/dlMN2SBKFLV9y2VfO8/xlmYcEOzVqlXNVjoGdWedaeT\nBcLFVEBDLykIfmeDm+lrmU/657HNvwJYy+ctSLIikYOplT3ULYzjufAXmD489z0g\nQ+Lcnsn80geo84mX1iCLnfeR\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-8f49g@dwi-license.iam.gserviceaccount.com",
  "client_id": "111248139098610310989",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-8f49g%40dwi-license.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
})

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://dwi-license-default-rtdb.firebaseio.com/"
})

ref = db.reference("/")
MAC_add = hex(get_mac())[2:].upper()
MAC_add = "-".join(MAC_add[i:i+2] for i in range(0, len(MAC_add), 2))
if MAC_add not in ref.get():
    print("Invalid License")
    sys.exit()
else:
    print("Confirmed License")


class Pipeline:
	def __init__(self):
		self.premier_folder = ""
		self.SEPERATOR = "__________________________________"
		self.direction_omitter = {}

	def get_premier_folder(self):
		self.premier_folder = filedialog.askdirectory(title="Select folder containing scans.")
		print("Selected: " + os.path.abspath(self.premier_folder))
		self.dti_instance = DTI(self.premier_folder)
		print(self.SEPERATOR + "\n")

	def get_output_folder(self):
		self.output_folder = filedialog.askdirectory(title="Select output_folder")
		print("Selected: " + os.path.abspath(self.premier_folder))
		self.dti_instance.output_folder = self.output_folder
		print(self.SEPERATOR + "\n")

	def save_nifti(self, img, OUTPUT_PATH):
		nib.save(img, OUTPUT_PATH)

	def run_quality_checker(self):
		print("Creating quality_checkers...", end="")
		for scan, numb in self.dti_instance.dti_scans.items():
			OUTPUT_DIR = os.path.join(self.output_folder, os.path.basename(scan))
			if not os.path.isdir(OUTPUT_DIR):
				os.mkdir(OUTPUT_DIR)
			for idx, img in enumerate(self.dti_instance.dti_imgs[scan]):
				path = os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_" + os.path.basename(numb[idx]) + ".nii")
				self.save_nifti(img, path)
				qual = qualityChecker(path)
				qual.run()
				self.direction_omitter[os.path.basename(path)] = qual.directions
		print("Done")
		plt.close()
		print(self.SEPERATOR + "\n")

	def getParameters(self):
		questions = [iq.Checkbox('Saves',
							message="What files do you want to save?",
							choices=['Anatomy', 'FA', 'ADC', 'b0', "RD"],
							),]
		answers = iq.prompt(questions)
		return answers["Saves"]

	def parse_parameters(self):
		parameters = self.getParameters()

		self.bool_anatomy = False
		self.bool_fa = False
		self.bool_adc = False
		self.bool_b0 = False
		self.bool_rd = False

		if "Anatomy" in parameters:
			self.bool_anatomy = True
		if "FA" in parameters:
			self.bool_fa = True
		if "ADC" in parameters:
			self.bool_adc = True
		if "b0" in parameters:
			self.bool_b0 = True
		if "RD" in parameters:
			self.bool_rd = True

	def save_files(self):
		for scan, numb in self.dti_instance.dti_scans.items():
			OUTPUT_DIR = os.path.join(self.output_folder, os.path.basename(scan))
			if numb:
				if self.bool_fa or self.bool_adc or self.bool_b0:
					for number in numb:
						img = nib.load(os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+".nii"))
						dim = self.dti_instance.getVoxelSize(number)
						method_file = os.path.join(number, "method")
						self.dti_instance.generate_bvals(method_file, OUTPUT_DIR, (os.path.basename(scan) + "_"+str(os.path.basename(number))+".nii"), self.direction_omitter[(os.path.basename(scan) + "_"+str(os.path.basename(number))+".nii")])
						tenfit = self.dti_instance.dti_fit(OUTPUT_DIR, img, (os.path.basename(scan) + "_"+str(os.path.basename(number))+".nii"))
						if self.bool_b0:
							b0 = nib.Nifti1Image(img.get_fdata()[:,:,:,0], None)
							b0.header["pixdim"][1] = dim[0]
							b0.header["pixdim"][2] = dim[1]
							b0.header["pixdim"][3] = dim[2]
							nib.save(b0, os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_b0.nii"))
							print("Saved " + os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_b0.nii"))
						if self.bool_fa:
							fa = nib.Nifti1Image(tenfit.fa, None)
							fa.header["pixdim"][1] = dim[0]
							fa.header["pixdim"][2] = dim[1]
							fa.header["pixdim"][3] = dim[2]
							fa.header["pixdim"][4] = dim[3]
							nib.save(fa, os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_fa.nii"))
							print("Saved " + os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_fa.nii"))
						if self.bool_rd:
							rd = nib.Nifti1Image(tenfit.rd, None)
							rd.header["pixdim"][1] = dim[0]
							rd.header["pixdim"][2] = dim[1]
							rd.header["pixdim"][3] = dim[2]
							rd.header["pixdim"][4] = dim[3]
							nib.save(rd, os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_rd.nii"))
							print("Saved " + os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_rd.nii"))
						if self.bool_adc:
							md = nib.Nifti1Image(tenfit.md, None)
							md.header["pixdim"][1] = dim[0]
							md.header["pixdim"][2] = dim[1]
							md.header["pixdim"][3] = dim[2]
							md.header["pixdim"][4] = dim[3]
							nib.save(md, os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_adc.nii"))
							print("Saved " + os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_adc.nii"))
				if self.bool_anatomy:
					number = self.dti_instance.rare_scans[scan]
					dim = self.dti_instance.getVoxelSize(number)
					img_anat = self.dti_instance.rare_imgs[scan]
					#nib.load(os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+".nii"))
					img_anat.header["pixdim"][1] = dim[0]
					img_anat.header["pixdim"][2] = dim[1]
					img_anat.header["pixdim"][3] = dim[2]
					nib.save(img_anat, os.path.join(OUTPUT_DIR, os.path.basename(scan) + "_"+str(os.path.basename(number))+"_anat.nii"))
					print("Saved " + str(os.path.join(OUTPUT_DIR, os.path.basename(scan) +"_"+str(os.path.basename(number))+"_anat.nii")))


	def introduction(self):
		subprocess.run("clear", shell=True)

		
		title = """
  ____ _____ ___   ____  _            _ _
 |  _ \_   _|_ _| |  _ \(_)_ __   ___| (_)_ __   ___
 | | | || |  | |  | |_) | | '_ \ / _ \ | | '_ \ / _ \ \n | |_| || |  | |  |  __/| | |_) |  __/ | | | | |  __/
 |____/ |_| |___| |_|   |_| .__/ \___|_|_|_| |_|\___|
						  |_|
 Created by Atul Phadke
		"""

		description = """

 This pipline contains all of the following features,
 1. Conversion between BRUKER and NIFTI file types
 2. DTI and generating FA, ADC, MD, etc.

		"""

		print(title)
		print(description)

		print("We would now like to input the files, \nPress enter to continue: ", end="")

		if input() != "":
			quit()
		else:
			print(self.SEPERATOR + "\n")

	def run(self):
		self.introduction()
		self.get_premier_folder()
		self.get_output_folder()
		self.run_quality_checker()
		self.parse_parameters()
		self.save_files()
		quit()


instance = Pipeline()
instance.run()

"""

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

"""

#print(dti_scans)
