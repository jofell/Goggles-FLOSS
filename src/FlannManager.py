#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2010 GSyC/LibreSoft, Universidad Rey Juan Carlos
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Author : Roberto Calvo Palomino <rocapal__at__libresoft__dot__es>
#


from pyflann import *
from numpy import *
from numpy.random import *
import cPickle as pickle  
import StringIO, string
import json

import cv
import sys
import os
import time
import subprocess

class FlannManager (object):
	
	def __init__(self):
		self.default_flags = ['C_CONTIGUOUS', 'ALIGNED']
		self.key_point_list = []
		self.myflann = None

		self.size_keypoint = 128
		self.num_clusters = 7000
		
		self.max_keypoints = 0
		
		self.flann_path = "/tmp/flann_data/"
		self.flann_descriptors = "descriptors/"
		self.flann_vwords = "vwords/"
		
		self.lemur_path = "/tmp/lemur_data/"
		self.lemur_bin_path = "/usr/local/bin/"
		
		
		# Delete old dirs and create it
		os.system("rm -rf %s" %(self.flann_path + self.flann_descriptors))
		if not os.path.exists(self.flann_path + self.flann_descriptors):
			os.makedirs(self.flann_path + self.flann_descriptors)
		
		os.system("rm -rf %s" %(self.flann_path + self.flann_vwords))
		if not os.path.exists(self.flann_path + self.flann_vwords):
			os.makedirs(self.flann_path + self.flann_vwords)	
			

		os.system("rm -rf %s" %(self.lemur_path))
		os.makedirs(self.lemur_path)	
		
		
	def __get_key_points(self, image_path):
		
		DESCRIPTORS_MIN = 300
		DESCRIPTORS_MAX = 420
		
		keypoints = 0
		descriptors = 0
		
		range = 600
		range_gap = 40
		do_surf = True
		
		image = cv.LoadImage(image_path, cv.CV_LOAD_IMAGE_GRAYSCALE)
			
		
		while (do_surf):

			(keypoints, descriptors) = cv.ExtractSURF(image, None, cv.CreateMemStorage(), (1, range, 3, 1))
			do_surf = False
			
			print "Descriptors: %d (range=%d)" % (len(descriptors),range)
			
			if (len(descriptors) < DESCRIPTORS_MIN):
				range = range - range_gap
			
			if ( len(descriptors) > DESCRIPTORS_MAX):
				range = range + range_gap

			if ( len(descriptors) >= DESCRIPTORS_MIN and len(descriptors) <= DESCRIPTORS_MAX):
				do_surf = False

		
		return (keypoints, descriptors)
			
	def add_photo (self, id, path):
				
		try:
			(keypoints, descriptors) = self.__get_key_points(path)
			
			image_name = str(id) + "-" + os.path.basename(path)
			# Save the descriptors in hard disk
			f = file (self.flann_path + self.flann_descriptors + image_name + ".keypoints", "w")
			pickle.dump(descriptors, f)
			f.close()

			print "* Photo %s with %d keypoints has been added" % (image_name, len(descriptors))
			self.key_point_list.extend(descriptors)
			
			if len(descriptors) > self.max_keypoints:
				self.max_keypoints = len(descriptors)
			
			return True
			
		except:
			print "Error while analazing " + image_name
			return False
		
	

	def set_number_clusters (self, num_clusters):
		self.num_clusters = num_clusters
		
		
	def set_flann_path (self, path):
		self.flann_path = path
	
	def create_index (self):
		
		try:
			print "Inside create_index ... "
			print "Max image keypoints: %d" % (self.max_keypoints) 
			
			print "Create a copy of dataset in array with float32 type"
			key_point_array = require(self.key_point_list, float32, self.default_flags)
			npts, dim  = key_point_array.shape
			
			print "In this variable will be saved the cluster centers"
			result = empty( (self.num_clusters, dim), dtype=float32)
			
			print "Clustering"
			myparams = FLANNParameters()
			#flann.compute_cluster_centers(key_point_array, len(key_point_array), self.size_keypoint, self.num_clusters, result, myparams)
			flann.compute_cluster_centers[key_point_array.dtype.type](key_point_array, len(key_point_array), self.size_keypoint, self.num_clusters, result, myparams)

			print "Index the cluster centers obtain in 'result'"
			self.myflann = FLANN()
			params = self.myflann.build_index(result, target_precision=0.9, log_level = "info" )

		
			print "Write the flann files"
			ls = os.listdir(self.flann_path + self.flann_descriptors)
			for fdescriptors in ls:
				
				f = file (self.flann_path + self.flann_descriptors + fdescriptors, "r")
				descriptors = pickle.load(f)
				f.close()
				
				vwords = self.__get_visual_words (descriptors)
				self.__write_visual_words (self.flann_path + self.flann_vwords + fdescriptors + ".flann", fdescriptors, vwords, False)
				
			print "Generate files.list to Lemur index"
			f = file (self.flann_path + "files.list", "w")
			ls = os.listdir(self.flann_path + self.flann_vwords)
			
			for file_name in ls:
				f.write(self.flann_path + self.flann_vwords + file_name + "\n")
			f.close()
				
			print "Generate the LEMUR index"
			self.__lemur_create_index(self.flann_path + "vwords", self.lemur_path + "index")
			
			try:
				retcode = subprocess.call([self.lemur_bin_path + "IndriBuildIndex", self.lemur_path + "builder.xml" ])
				if retcode != 0:
					print "! Error while executing BuildIndex Lemur"
			except:
				print "! Exception ocurred in BuildIndex Lemur subprocess"
		except:
			import traceback
			traceback.print_exc(file=sys.stdout)
		
		
	def __lemur_create_index(self, path_file_list, path_dest_index):
		
		f = open ("../conf/builder.xml","r")
		builder_xml = f.read()
		builder_xml = (builder_xml.replace("$PATH_FILE_LIST",path_file_list)).replace("$PATH_DEST_INDEX",path_dest_index)
		f.close()
		
		f = open (self.lemur_path + "builder.xml","w")
		f.write(builder_xml)
		f.close()
		
	def __lemur_create_query (self, path_index_key, path_query, path_result, number_results):
		
		f = open ("../conf/query.xml","r")
		query_xml = f.read()
		query_xml = (query_xml.replace("$PATH_INDEX_KEY",path_index_key)).replace("$PATH_QUERY",path_query)
		query_xml = (query_xml.replace("$PATH_RESULT",path_result)).replace("$NUMBER_RESULTS",number_results)
		f.close()
		
		f = open (self.lemur_path + "query.xml","w")
		f.write(query_xml)
		f.close()
	
	
	def __list_to_json (self, list):
			
		json = "{ \"code\" : \"200\" , \"results\": ["
		
		for node in list:
			try:
				id = (node[0]).split("-")[0]
				range = (node[1])
				json = json  +  "{\"id\": \"" + id + "\", \"range\" : \"" + range + "\" },"
				
			except:
				None
        
		json = json[0:-1]
		json = json + "]}"
		return json	

	def query (self, image_path):
		(keypoints, descriptors) = self.__get_key_points(image_path)		

		image_name = os.path.basename(image_path)	

		vwords = self.__get_visual_words(descriptors)
		#self.__write_visual_words ("/tmp/query.flann", image_name, vwords, True)
		#self.__write_visual_words2 ("/tmp/query2.flann", image_name, vwords)
		
		sometext = ""

		for i in range(len(vwords)):
			sometext += (str(vwords[i])).strip(']').strip('[')
			sometext += " "
		
		self.__lemur_create_query (self.lemur_path + "index", sometext, self.lemur_path + "result","10")
		try:

			out_result = StringIO.StringIO()
			from subprocess import Popen, PIPE, STDOUT

			# f = open (self.lemur_path + "result","w")
			
			p = subprocess.Popen([self.lemur_bin_path + "IndriRunQuery", self.lemur_path + "query.xml" ], 
				stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
			
			result_str = p.stdout.read()

			#print out_result.getvalue()
			#if retcode != 0:
			#	print "! Error while executing RetEval Lemur"
			#print out_result.getvalue()
			#f.close()
				
			# Parser the result
			# f = open (self.lemur_path + "result","r")
			# result_str = f.read()
			# f.close()
			
			#print result_str
			result = result_str.split("\n")
			# Delete the last item that is ""
			result.pop()
			
			list = []
					
			for res in result:
				try:
					name = res.split(" ")[2]
					score = res.split(" ")[4]
					list.append ((name,score))
					
				except:
					print "! Error while obtain data (result)"
					import traceback
					traceback.print_exc()

			print list

			return_str = self.__list_to_json(list)
			
			return return_str
			
		except:
			print "! Exception ocurred in RetEval Lemur subprocess"
			import traceback
			traceback.print_exc()
			
		
	def console (self):
		
		print "Init console ...\n"
		flag = True
		while flag:
			command = raw_input("$> ")
			if command == "exit":
				return
			else:
				start = time.time ()
				result = self.query(command)
				end = time.time ()
				elapsed = end - start;
				
				print "Query done in %f sec" % (elapsed)
				
				print "\n"
				print result
				
				
	def __get_visual_words(self, descriptors):		
	
		key_point_array = require(descriptors, float32, self.default_flags)
		nqpts = key_point_array.shape[0]
		dim = key_point_array.shape[1]

		num_neighbors = 1
	
		vwords = empty( (nqpts, num_neighbors), dtype=index_type)
		dists = empty( (nqpts, num_neighbors), dtype=float32)
	
		myparams = FLANNParameters()
	
		#flann.flann_find_nearest_neighbors_index(self.myflann._FLANN__curindex, key_point_array, nqpts, vwords, dists, num_neighbors, myparams['checks'] ,myparams)
		flann.find_nearest_neighbors_index[key_point_array.dtype.type](self.myflann._FLANN__curindex,
                    key_point_array, nqpts,
                    vwords, dists, num_neighbors,
                    myparams)
		#print (vwords, dists)
		return vwords
	
	
	def __write_visual_words (self, nameFile, nameImage, vocabulary, query):

		f = open(nameFile,"w")
		
		if (query):
			f.write("<DOC 1>\n")
		else:	
			f.write("<DOC>\n")
			f.write("<DOCNO>")
			f.write(nameImage)
			f.write("</DOCNO>\n")
			
		f.write("<TEXT>\n")
	
		for i in range(len(vocabulary)):
			f.write(str(vocabulary[i]).strip(']').strip('['))
			f.write(" ")
	
		f.write("\n")
		
		f.write("</TEXT>\n")
			
		f.write("</DOC>\n")
		
		f.close()

	def __write_visual_words2 (self, nameFile, nameImage, vocabulary):
		
		f = open(nameFile,"w")
		
		f.write("<DOC 1>\n")
		
		for i in range(len(vocabulary)):
			f.write("The mapped cluster %s for the key point\n" % (str(vocabulary[i]).strip(']').strip('[')))
			
		
		f.write("</DOC>\n")
		f.close()
