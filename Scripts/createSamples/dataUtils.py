# -*- coding: utf-8 -*-
from nltk.tokenize import word_tokenize
import os
import sys
import random
import time
from collections import defaultdict


###reads in filename and overwrites it with a new file in which every line has tag written preceding it		
def prependTagsToLines(tag,fileName):
	file = open(fileName,'r')
	lines =file.readlines()
	file.close()
	outFile = open(fileName,'w')
	for line in lines:
		outFile.write(tag + ' ' + line)
	outFile.close()

###samples numVerse verses from possible pairs and removes all versions of them from possible pairs
###writes a file for each version of the bible containing the sample verses.  These files have numVerse lines and are all parallel to one another
def allVersionSample(possiblePairs, numVerse, inputFolder,outPutFolder, sampleNameForOutFiles):
	if not os.path.exists(outPutFolder):
		os.mkdir(outPutFolder)
	versionList = os.listdir(inputFolder)
	versionDict = {}

	for version in versionList:
		versionDict[version] = open(os.path.join(outPutFolder,sampleNameForOutFiles + version + '.txt'),'w')
	for i in range(numVerse):
		sampleBook,sampleChapter,sampleVerse,sampleNVersion,sampleSimVersion = selectNewPair(possiblePairs,True)
		for version in versionList:
			text,sameText = readChosenPair(sampleBook,sampleChapter,sampleVerse,version,version,inputFolder,inputFolder)
			if text != None:
				versionDict[version].write(text)
			versionDict[version].write('\n')


#writes out (but does not remove) all pairs in possible pairs of sourceversion->target version
#writes to two files, outName.sourc and outName.tgt
#if removeFromPairs=True then it does remove these versions of the verses from possible pairs (but not other versions of those same verses)
#inputFolder is the base directory housing the bible texts
def writeRemainingPairsFromVersions(possiblePairs,outName,sourceVersion,targetVersion, inputFolder, removeFromPairs = False):
	sourceOutFile = open(outName + '.sourc','w')
	targetOutFile = open(outName + '.tgt','w')

	for book in possiblePairs:
		for chapter in possiblePairs[book]:
			for verseNum in possiblePairs[book][chapter]:
				if sourceVersion in possiblePairs[book][chapter][verseNum] and targetVersion in possiblePairs[book][chapter][verseNum][sourceVersion]:
					targetText,sourceText = readChosenPair(book,chapter,verseNum,sourceVersion,targetVersion,inputFolder,inputFolder)

					if removeFromPairs:
						possiblePairs[book][chapter][verseNum][sourceVersion].remove(targetVersion)
					
					if sourceText != None and targetText!=None:
						sourceOutFile.write(sourceText )
						sourceOutFile.write('\n')
						targetOutFile.write(targetText)
						targetOutFile.write('\n')

##returns a nested series of dictionaries with keys of book->chapter->verseNum->sourceVersion = targetVersion 
##Dictionary contains all valid pairings from the targetFolderName and sourceFolderName, assuming they have the same directory structure
## exclude can be used to specify a list of versions in exclude which we should not make pairs for
def buildPossiblePairs(targetFolderName,sourceFolderName,exclude = []):
	
	possiblePairs = {}
	totalPairs = 0
	print "About to make all possible pairs"
	t0 = time.time()
	targetFolder = os.path.join(targetFolderName)
	sourceFolder = os.path.join(sourceFolderName)
	for root, subdirs, files in os.walk(targetFolder):
		for file in files:
			parts = root.split(os.sep)
			targetVersion,book,chapter = parts[-2],parts[-1],file
			if book not in possiblePairs: 
				possiblePairs[book] = {}
			if chapter not in possiblePairs[book]:
				possiblePairs[book][chapter] = {}

			targetFile = open(os.path.join(root,file),'r')
			targetLines=targetFile.readlines()
			targetFile.close()
			for line in range(len(targetLines)):
				if str(line) not in possiblePairs[book][chapter]:
					possiblePairs[book][chapter][str(line)] = defaultdict(list)
			for sourceVersion in os.listdir(sourceFolder):
				if sourceVersion not in exclude and targetVersion not in exclude:
					if os.path.exists(os.path.join(sourceFolder,sourceVersion,book,chapter)):
						sourceFile = open(os.path.join(sourceFolder,sourceVersion,book,chapter),'r')
						sourceLines = sourceFile.readlines()
						sourceFile.close()
						for i in range(min(len(sourceLines),len(targetLines))):
							possiblePairs[book][chapter][str(i)][sourceVersion].append(targetVersion)
							totalPairs +=1

	print "Done with making possible pairs. It took " + str(time.time()-t0) + "seconds."
	print str(totalPairs) + " possible pairs." 
	return possiblePairs



#######chooses and write numVerses pairs from those remaining in the nested dictionary(as created by buildPossiblePairs) of bible verses
#######Removes all occurrences of this verse in any version from possiblePairs if removeAllVerseOccurrences is true and only the selected pair of the verse otherwise
#######Writes every targetVersion to refOutputFolder for eventual multi-bleu scoring
#######If refVersion is not None then it should be some target version.  This will make the verses selected and written to targetOutFile always be from refVersion
####### returns possiblePairs with the sampled pairs removed
##### removeAllOccurrences must be True if refVersion is set
##### if sourceVersion is not none then all selected pairs will be from that source version(intended to be used when refversion is also set)
def chooseAndWritePairs(numVerses, sampleName, possiblePairs, inputFolder,inputFolder2,outputFolder, removeAllVerseOccurrences = False, refOutputFolder = None, refVersion=None, sourceVersion=None):
	targetOutFile = open(os.path.join(outputFolder,sampleName + '.tgt'),'w')
	sourceOutFile = open(os.path.join(outputFolder,sampleName + '.sourc'),'w')
	while numVerses>0 and len(possiblePairs.keys())>0:
		
		targetText = None
		sourceText = None
		while targetText == None and len(possiblePairs.keys())>0:
			sampleBook,sampleChapter,sampleVerse,sampleSourceVersion,sampleTargetVersion = selectNewPair(possiblePairs,removeAllVerseOccurrences,refVersion,sourceVersion)
			if sampleBook != None:
				targetText,sourceText = readChosenPair(sampleBook,sampleChapter,sampleVerse,sampleSourceVersion,sampleTargetVersion,inputFolder,inputFolder2)
			

		if targetText == None:
			continue

		numVerses = numVerses-1
		targetOutFile.write(targetText + '\n')
		sourceOutFile.write("<" +sampleTargetVersion + "> " + sourceText + '\n')


	sourceOutFile.close()
	targetOutFile.close()
	


#####selects one pair of verses from possible Pairs
#####removes all other occurrences of that verse from possible pairs if removeAllVerseOccurrences
##### if refVersion is specified it will always select that as the target Version 
##### if sourceVersion is specified it will always select that version for source part of pair
##### removeAllOccurrences must be True if refVersion is set
#### returns Book, Chapter,Verse,sourceVersion,targetVersion of selected pair
def selectNewPair(possiblePairs,removeAllVerseOccurrences,refVersion = None,sourceVersion=None):
	
	
	found = False

	while not found and len(possiblePairs.keys())!=0 :
		sampleBook = random.choice(possiblePairs.keys())
		
		if len(possiblePairs[sampleBook]) ==0:
			del possiblePairs[sampleBook]
			continue
		sampleChapter = random.choice(possiblePairs[sampleBook].keys())
		if len(possiblePairs[sampleBook][sampleChapter]) == 0:
			del possiblePairs[sampleBook][sampleChapter]
			continue
		sampleVerse = random.choice(possiblePairs[sampleBook][sampleChapter].keys())
		if len(possiblePairs[sampleBook][sampleChapter][sampleVerse]) == 0:
			del possiblePairs[sampleBook][sampleChapter][sampleVerse]
			continue
		if sourceVersion ==None:
			sampleSourceVersion = random.choice(possiblePairs[sampleBook][sampleChapter][sampleVerse].keys())
		else:
			sampleSourceVersion = sourceVersion
		if len(possiblePairs[sampleBook][sampleChapter][sampleVerse][sampleSourceVersion]) == 0:
			del possiblePairs[sampleBook][sampleChapter][sampleVerse][sampleSourceVersion]
			continue

		if refVersion == None:
			sampleTargetVersion = random.choice(possiblePairs[sampleBook][sampleChapter][sampleVerse][sampleSourceVersion])
		else:
			sampleTargetVersion = refVersion
			if sampleTargetVersion not in possiblePairs[sampleBook][sampleChapter][sampleVerse][sampleSourceVersion]:
				del possiblePairs[sampleBook][sampleChapter][sampleVerse]
				return None,None,None,None,None

		possiblePairs[sampleBook][sampleChapter][sampleVerse][sampleSourceVersion].remove(sampleTargetVersion)

		if removeAllVerseOccurrences:
			del possiblePairs[sampleBook][sampleChapter][sampleVerse]
		found = True
	if found:
		return sampleBook,sampleChapter,sampleVerse,sampleSourceVersion,sampleTargetVersion
	return None,None,None,None,None



##reads  the pair specified by parameters
##returns the text of the targetVerse and the text of the sourceVerse
## if the verse numbers aren't the same or the line is empty or something returns None,None
##inputFolder is the houses the target version texts, inputFolder 2 holds the source versions
def readChosenPair(sampleBook,sampleChapter,sampleVerse,sampleSourceVersion,sampleTargetVersion,inputFolder,inputFolder2):
	targetFile = open(os.path.join(inputFolder,sampleTargetVersion ,sampleBook,sampleChapter),'r')
	sourceFile = open(os.path.join(inputFolder2,sampleSourceVersion , sampleBook,sampleChapter),'r')

	targetLines = targetFile.readlines()
	sourceLines = sourceFile.readlines()

	verse = (int)(sampleVerse)
	try:
		if targetLines[verse].split(" ") [0] != sourceLines[verse].split(" ")[0] or targetLines[verse] == "" or sourceLines[verse]== "":
			return None,None
		else:
			targetText = targetLines[verse].strip()
			sourceText = sourceLines[verse].strip()
			
			return targetText,sourceText		
	except IndexError:
		return None,None

	finally:
		targetFile.close()
		sourceFile.close()
		

### Reads in originalFileNameSource and originalFileNameTarget which have potentially many versions of verses each tagged with <BBE> style tag
### finds all lines with targetVersion as the tag and writes new output pair of files with only those lines 
def makeSingleTargetDataSet(originalFileNameSource, originalFileNameTarget, outputFileNameSource, outPutFileNameTarget, targetVersion):
	sourceFile = open(originalFileNameSource,'r')
	targetFile = open(originalFileNameTarget,'r')
	outSourceFile = open(outputFileNameSource,'w')
	outTargetFile = open(outPutFileNameTarget,'w')
	#print outputFileName

	sourceLines = sourceFile.readlines()
	targetLines = targetFile.readlines()

	for i in range(len(sourceLines)):
		line = sourceLines[i]
		tag = line.split(' ')[0]
		if '<' + targetVersion + '>' == tag:
			
			outSourceFile.write(line)
			outTargetFile.write(targetLines[i])

	sourceFile.close()
	targetFile.close()
	outSourceFile.close()
	outTargetFile.close()

#overwrites the file called fileName with a version of itself which does not have the verse numbers at the start of each line.
def removeVerseNumbers(fileName):
	lines = open(fileName,'r').readlines()
	outFile = open(fileName,'w')
	for line in lines:
		parts = line.split(" ")
		if parts[0].isdigit():
			del parts[0]
		elif len(parts)>1 and parts[1].isdigit():
			del parts[1]

		newLine = ' '.join(parts)
		
		outFile.write(newLine)
	outFile.close()

## removes <BBE> style tags from filename writes stripped version to outPutFileName
def stripTargetTags(fileName,outPutFileName):
	inFile = open(fileName,'r')
	outFile = open(outPutFileName,'w')
	lines = inFile.readlines()
	for i in range(len(lines)):
		line = lines[i]
		tag = line.split(' ')[0]
		if tag[0] == '<' and tag[-1] =='>':
			lines[i]=line[len(tag)+1:]
	for line in lines:
		outFile.write(line)

	inFile.close()
	outFile.close()

