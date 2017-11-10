
import subprocess
import os
import dataUtils
from shutil import copyfile

#path to repository
repositoryDir = '/home/kcarlson/Zero-Shot-Style-Transfer'


sourceVersion = "ASV"
targetVersion = "BBE"
devSampleSize = 200
mosesDevSampleSize = 1000
testSampleSize = 200
trainSampleSize = 500000


#parent directory that will hold all Data
baseDataDir = os.path.join(repositoryDir,'Data')

###folder that will house all output from this sampling run
baseSampleOutDir = os.path.join(baseDataDir,'Sample')

##directory that holds data scripts used and also has subword-nmt directory with its scripts
scriptDir = os.path.join(repositoryDir,'Scripts','createSamples')

#directory with subwordNMT project with bpe code
subWordNMTDir = os.path.join(scriptDir,'subword-nmt-master')

####### folder for unmodified samples to be written to 
sampleFolder  =  os.path.join(baseSampleOutDir,'rawSamples')

#######folder with simply tokenized bibles for sampling
bibleSimpleTokenDir = os.path.join(baseDataDir,'Bibles')

##folder to output all versions of the dev verses
devOutFolder = os.path.join(sampleFolder,'devSet')

##folder to output all versions of the test verses
testOutFolder = os.path.join(sampleFolder,'testSet')

##folder to output all verses from source version to target which weren't in test or dev
zeroShotRestFolder = os.path.join(sampleFolder,'RemainingSourceTargetPairs')

#folder to hold BPE tokenized outputs
BPETokenizedDir = os.path.join(baseSampleOutDir,'BPETokenizedSample')

#name of the bpe vocab file
bpeCodeFileName =  os.path.join(baseDataDir,'Vocab','subWords.bpe')

##name of directory for all samples for moses to be output to
mosesSampleDir = os.path.join(baseSampleOutDir,'MosesSamples')

##name of directory for all samples for seq2seq to be output to
seq2SeqSampleDir = os.path.join(baseSampleOutDir,'Seq2SeqSamples')


#########################Execution####################
#Build nested dictionary of all possible pairs of verses
possiblePairs = dataUtils.buildPossiblePairs(bibleSimpleTokenDir,bibleSimpleTokenDir)


#make sure the directory structure we need exists

if not os.path.exists(baseSampleOutDir):
	os.mkdir(baseSampleOutDir)

if not os.path.exists(sampleFolder):
	os.mkdir(sampleFolder)
if not os.path.exists(devOutFolder):
	os.mkdir(devOutFolder)
if not os.path.exists(testOutFolder):
	os.mkdir(testOutFolder)

if not os.path.exists(zeroShotRestFolder):
	os.mkdir(zeroShotRestFolder)

if not os.path.exists(BPETokenizedDir):
	os.mkdir(BPETokenizedDir)

if not os.path.exists(mosesSampleDir):
	os.mkdir(mosesSampleDir)

if not os.path.exists(seq2SeqSampleDir):
	os.mkdir(seq2SeqSampleDir)


#create test sample, writing all versions of the selected verses and removing them from possible pairs
print "About to make test and dev sets"
dataUtils.allVersionSample(possiblePairs,testSampleSize,bibleSimpleTokenDir, testOutFolder, 'zeroShotTest')

#create development sample
dataUtils.allVersionSample(possiblePairs,devSampleSize,bibleSimpleTokenDir, devOutFolder, 'zeroShotDev')

#write out all verses of the zero-shot source-target which do not appear in test or dev.  Remove the pairsings from possible pairs
dataUtils.writeRemainingPairsFromVersions(possiblePairs,os.path.join(zeroShotRestFolder,'unusedSourceTargetPairs'),sourceVersion,targetVersion,bibleSimpleTokenDir, removeFromPairs=True)

#sample verses of zero-shot target to use for tuning Moses language model.  Remove all versions of selected verses from possible pairs

dataUtils.chooseAndWritePairs(mosesDevSampleSize, 'devForMoses', possiblePairs , bibleSimpleTokenDir, bibleSimpleTokenDir, sampleFolder,
									refOutputFolder = '',removeAllVerseOccurrences = True, refVersion = targetVersion)

print "About to create training set"
#create training sample by selecting from verse pairs remaining in possiblePairs
dataUtils.chooseAndWritePairs(trainSampleSize, 'zeroShotTrain', possiblePairs , bibleSimpleTokenDir, bibleSimpleTokenDir, sampleFolder)


#remove all verse numbers from all samples
print "About to remove verse numbers from samples"
for entry in os.listdir(sampleFolder):  
	if os.path.isfile(os.path.join(sampleFolder,entry)):
		dataUtils.removeVerseNumbers(os.path.join(sampleFolder,entry))
	if os.path.isdir(os.path.join(sampleFolder,entry)):
		for file in os.listdir(os.path.join(sampleFolder,entry)):
			dataUtils.removeVerseNumbers(os.path.join(sampleFolder,entry,file))


print "Cleaning up samples for Moses"

#remove <target> tags from the sample that will fine tune language model in moses
dataUtils.stripTargetTags(os.path.join(sampleFolder,'devForMoses.sourc'),os.path.join(mosesSampleDir,'dev.sourc'))


###look through training sample and copy all pairs which have the zero-shot target.  This is what we will use to train Moses.
dataUtils.makeSingleTargetDataSet(os.path.join(sampleFolder,'zeroShotTrain.sourc'), os.path.join(sampleFolder,'zeroShotTrain.tgt'), os.path.join(mosesSampleDir,'zeroShotTrainTargetVersionOnlyWithTags.sourc'), os.path.join(mosesSampleDir,'train.tgt'), targetVersion)

#remove <target> tags from the Moses training sample
dataUtils.stripTargetTags(os.path.join(mosesSampleDir,'zeroShotTrainTargetVersionOnlyWithTags.sourc'),os.path.join(mosesSampleDir,'train.sourc'))

os.remove(os.path.join(mosesSampleDir,'zeroShotTrainTargetVersionOnlyWithTags.sourc'))	


#move files to the moses sample directory							
copyfile(os.path.join(sampleFolder,'devForMoses.tgt'),os.path.join(mosesSampleDir,'dev.tgt'))

copyfile(os.path.join(testOutFolder,'zeroShotTest' +sourceVersion + '.txt'),os.path.join(mosesSampleDir,'test.sourc'))

copyfile(os.path.join(testOutFolder,'zeroShotTest' + targetVersion + '.txt'),os.path.join(mosesSampleDir,'test.tgt'))





print "About to apply BPE vocab"

subprocess.call(['python', os.path.join(scriptDir,'massApplyBPE.py'),scriptDir,sampleFolder,BPETokenizedDir,bpeCodeFileName])



print "About to move needed files to Seq2Seq sample directory"
copyfile(os.path.join(BPETokenizedDir,devOutFolder[len(sampleFolder)+1:],'zeroShotDev' + sourceVersion+ '.txt'),os.path.join(seq2SeqSampleDir,'dev.sourc'))
copyfile(os.path.join(BPETokenizedDir,testOutFolder[len(sampleFolder)+1:],'zeroShotTest' + sourceVersion+ '.txt'),os.path.join(seq2SeqSampleDir,'test.sourc'))
copyfile(os.path.join(BPETokenizedDir,devOutFolder[len(sampleFolder)+1:],'zeroShotDev' + targetVersion+ '.txt'),os.path.join(seq2SeqSampleDir,'dev.tgt'))
copyfile(os.path.join(BPETokenizedDir,testOutFolder[len(sampleFolder)+1:],'zeroShotTest' + targetVersion+ '.txt'),os.path.join(seq2SeqSampleDir,'test.tgt'))
copyfile(os.path.join(BPETokenizedDir,'zeroShotTrain.sourc'),os.path.join(seq2SeqSampleDir,'train.sourc'))
copyfile(os.path.join(BPETokenizedDir,'zeroShotTrain.tgt'),os.path.join(seq2SeqSampleDir,'train.tgt'))


#add our target tags to test and dev for the seq2seq samples
dataUtils.prependTagsToLines('<' +targetVersion + '>',os.path.join(seq2SeqSampleDir,'test.sourc'))
dataUtils.prependTagsToLines('<' + targetVersion+'>',os.path.join(seq2SeqSampleDir,'dev.sourc'))

