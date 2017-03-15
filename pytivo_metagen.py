#!/usr/bin/python
# 
# Copyright (c) 2008, Graham Dunn <gmd@kurai.org>
# Copyright (c) 2009-2011, Josh Harding <theamigo@gmail.com>
# Copyright (c) 2016, George Stockfisch <gstock.public@gmail.com>
#
# Many part of the code was pulled/copied
# from https://sourceforge.net/projects/pytivometathis/
# So thank you, and including your copyright info above as well
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#    * Neither the name of the author nor the names of the contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# Version : $Id:$
# vim: autoindent tabstop=4 expandtab shiftwidth=4


import json
import optparse
import os
import sys
import ntpath
import re
import ConfigParser

import logging
import __builtin__
__builtin__.RPCLOGLEVEL = logging.INFO
import rpcSearch102

logging.basicConfig(format='%(message)s', level=logging.DEBUG)

# Regexes that match TV shows.
tvres = [r'(.+)[Ss](\d\d?)[Ee](\d+)', r'(.+?)(?: -)? ?(\d+)[Xx](\d+)', r'(.*).(\d\d\d\d).(\d+).(\d+).*', r'(.*).(\d+).(\d+).(\d\d\d\d).*', r'(?i)(.+)(\d?\d)(\d\d).*sitv']
# Types of files we want to get metadata for
fileExtList = [".mpg", ".avi", ".ogm", ".mkv", ".mp4", ".mov", ".wmv", ".vob", ".m4v", ".flv"]

TIVOUSERNAME = ""
TIVOPASSWORD = ""
TIVOTSN = ""

#################################################################################################
##
##  function: PPrintJson
##  purpose: pretty prints a jason string
##  parameters: jsonString - string: the string we want to print
##  returns: nothingepiiii
##
#################################################################################################
def PPrintJson( jsonString):
  if type(jsonString) is str:
    logging.debug(json.dumps(json.loads(jsonString), sort_keys=False, indent=4))
  else:
    logging.debug(json.dumps(jsonString, sort_keys=False, indent=4))
  return None

#################################################################################################
##
##  function: GetAllFiles
##  purpose: gets a list of all files in a directory, recursivly
##  parameters: directory - string: the directory we want to search for files in
##  returns: List: a list of files in the directory, including the path to the file
##
#################################################################################################
def GetAllFiles(directory):
	fileList = []
	"Get list of file info objects for files of particular extensions"
	dirAndFileList = os.listdir(directory)
	logging.debug(dirAndFileList)
	for singleObject in dirAndFileList:
		obectWithDir = os.path.join(directory, singleObject)
		if os.path.isdir(obectWithDir):
			#recursivly call this function to get all files
			fileList = fileList + GetAllFiles(obectWithDir)
		else:
			fileList.append(obectWithDir)
	return fileList

#################################################################################################
##
##  function: PruneFiles
##  purpose: strips out all files that are not a video, as well as all files that have an associated
##				.txt file, which should mean they have been parsed already
##  parameters: List - string: a list of files, including the full path
##  returns: List: a list of files that need to be searched, including the full path
##
#################################################################################################
def PruneFiles(fileList):

	prunedFiles = []
	for singleFile in fileList:
		if (os.path.splitext(singleFile)[1].lower() in fileExtList):
			#if there is a vid.txt file, then we can add it to the pruned list
			if (not singleFile + ".txt" in fileList ):
				prunedFiles.append(singleFile)
	return prunedFiles
	# fileList = [f for f in entries if os.path.splitext(f)[1].lower() in fileExtList and len(os.path.splitext(f)[0]) and os.path.isfile(os.path.join(directory, f))]
	# fileList.sort()
	# logging.debug("fileList after cull: %s" % str(fileList))
	# dirList = []
	# # Get a list of all sub dirs
	# dirList = [d for d in entries if os.path.isdir(os.path.join(directory, d)) and not d[0] == '.']
	# dirList.sort()
	# logging.debug("dirList after cull: %s" % str(dirList))
	# return (fileList, dirList)

#################################################################################################
##
##  function: WriteMetaFile
##  purpose: writes the metadata file out
##  parameters: filename - string: the name of the file to write
##				title - string: the show series
##				seriesID - string: the seriesID
##				programID - string: the programID
##				episodeTitle - string: the title of the episode
##				description - string: the episode description
##  returns: none
##
#################################################################################################
def WriteMetaFile(filename,title ,seriesID,programID,episodeTitle,description):
	outfile = open(filename, 'w')
	
	outfile.write("title : " + title + "\n")
	outfile.write("seriesTitle : " + title + "\n")
	outfile.write("episodeTitle : " + episodeTitle + "\n")
	outfile.write("seriesId : " + seriesID + "\n")
	outfile.write("programId : " + programID + "\n")
	outfile.write("description : " + description + "\n")

	outfile.close()
	return None

#################################################################################################
##
##  function: ProcessFiles
##  purpose: does the work of searching, and wrting txt files
##  parameters: List - string: a list of files, including the full path
##  returns: none
##
#################################################################################################
def ProcessFiles(fileList):
	for singleFile in fileList:
		fileName = ntpath.basename(singleFile)
		seriesIdFilename = ""
		logging.info("Going to process file: " +  fileName)
		(series, season, episode, year, month, day) = ParseFileInfo(fileName)
		seriesIdFilename = series + ".tivoSeriesId"
		seriesIdFileContents = None
		if ( os.path.isfile(seriesIdFilename) ):
			infile = open(seriesIdFilename, 'r')
			seriesIdFileContents = infile.read()
			infile.close()
		seriesID,programID =  SearchMind(series, season, episode, seriesIdFileContents)
		WriteMetaFile(fileName + ".txt" ,series,seriesID,programID,"Title should come from Tivo","Description should come from Tivo")
		if ( not os.path.isfile(seriesIdFilename) ):
			logging.info("Writing " + seriesIdFilename + " file")
			outfile = open(seriesIdFilename, 'w')
			outfile.write(seriesID)
			outfile.close()

#################################################################################################
##
##  function: SearchMind
##  purpose: searches tivo mind to get the seriesId and collectionId
##  parameters: seriesTitle - string: the series title we will be searching
##				seasonNumber - string: the season number we are going to search
##				episodeNumber - string: the episode number we are going to search
##				existingCollectionId - string: an existing series id from a previous run
##  returns: none
##
#################################################################################################
def SearchMind(seriesTitle, seasonNumber, episodeNumber , existingCollectionId=None):
	
	rpcSearch = rpcSearch102.Remote(TIVOUSERNAME,TIVOPASSWORD,TIVOTSN)
	searchType = 'contentSearch'
	
	#results = rpcSearch.seasonEpisodeSearch(seriesTitle,seasonNumber,episodeNumber,1)
	
	if ( existingCollectionId == None ):
		logging.debug("Need to search for a collection ID")
		collectionId = rpcSearch.GetCollectionID(seriesTitle)
		#collectionId = rpcSearch.GetCollectionID(seriesTitle, existingSeriesId)
	else:
		#tivo rpc needs the tivo.cl., tivo metadata needs SH
		collectionId = existingCollectionId.replace("SH","tivo:cl.")
	logging.debug( "COllection id we returned: " + collectionId)

	episodeEPGInfo = rpcSearch.EpisodeSearch(seriesTitle,collectionId,seasonNumber, episodeNumber)
	logging.info("episode info dump:")
	PPrintJson(episodeEPGInfo)
	seriesID = episodeEPGInfo['content'][0]['partnerCollectionId'].encode('utf8').replace('epgProvider:cl.','')
	programID = episodeEPGInfo['content'][0]['partnerContentId'].encode('utf8').replace('epgProvider:ct.','')
	logging.info("contentID: " + str(episodeEPGInfo['content'][0]['contentId']))
	logging.info("collectionId: " + str(episodeEPGInfo['content'][0]['collectionId']))
	logging.info("seriesID: " + seriesID)
	logging.info("programID: " + programID)
	return seriesID,programID
	
#################################################################################################
##
##  function: ParseFileInfo
##  purpose: parses the file name to get the info, series#, ep#, title, etc
##  parameters: regedx - string: a list of files, including the full path
##  returns: none
##
#################################################################################################
def ParseFileInfo(fileName):
	for tvre in tvres:
			match = re.search(tvre, fileName)
			if match:
				print "got match: " + str(match)
				series = re.sub('[._]', ' ', match.group(1)).strip()
			 	if match.lastindex >= 4:
					season = 0
					episode = 0
					if int(match.group(2)) >= 1000:
						year = str(int(match.group(2)))
						month = str(int(match.group(3)))
						day = str(int(match.group(4)))
					else:
						year = str(int(match.group(4)))
						month = str(int(match.group(2)))
						day = str(int(match.group(3)))
				else:
					season = str(int(match.group(2))) # strip out leading zeroes
					episode = str(int(match.group(3)))
					year = 0
					month = 0
					day = 0
			#I had an issue with Title.S02E04 coming out as "Title S" which is not right, so break after the first match for now
			break
			logging.debug("    Series: %s\n    Season: %s\n    Episode: %s\n    Year: %s\n    Month: %s\n    Day: %s" % (series, season, episode, year, month, day))
  	return series, season, episode, year, month, day

#################################################################################################
##
##  function: GetConfig
##  purpose: gets the config info
##  parameters: 
##  returns: the config info
##
#################################################################################################
def GetConfig():

	print "file: " + os.path.basename(__file__) + ".conf"
	with open(os.path.basename(__file__) + ".conf") as confFile:    
		data = json.load(confFile)
	tivoUsername = data['tivo_username']
	if (len(tivoUsername) < 1 or tivoUsername == '<tivo.com.username>'):
		logging.error("No username supplied in config file, exiting")
		exit(1)
	tivoPassword = data['tivo_password']
	if (len(tivoPassword) < 1 or tivoPassword == '<tivo.com.password>'):
		logging.error("No password supplied in config file, exiting")
		exit(1)
	tivoTsn = data['tivo_tsn']
	if (len(tivoTsn) < 1 or tivoTsn == '<tivo.tsn>'):
		logging.error("No tsn supplied in config file, exiting")
		exit(1)


	return tivoUsername,tivoPassword,tivoTsn
#################################################################################################
##
##  function: main
##  purpose: main function
##  parameters: 
##  returns: nothing
##
#################################################################################################
def main():
	global args
	global TIVOUSERNAME
	global TIVOPASSWORD
	global TIVOTSN

	parser = optparse.OptionParser(description='Gets metadata from tivo mind server')
	parser.add_option('--folder', '-f', dest='folder',
			help='folder to search for new metadata')
	# parser.add_option('--parse', '-p', dest='parse',
	# 		help='parse folder')
	
	options, args = parser.parse_args()

	if ( options.folder == None ):
		logging.error("ERROR: You must supply a folder to search")
		parser.print_help()
		sys.exit(1)
	

	TIVOUSERNAME,TIVOPASSWORD,TIVOTSN = GetConfig()
	allFilesList = GetAllFiles(options.folder)
	logging.debug("All Files: " + str(allFilesList))
	prunedFileList = PruneFiles(allFilesList)
	logging.debug("Pruned Files: " + str(prunedFileList))
	ProcessFiles(prunedFileList)

if __name__ == "__main__":
	main()