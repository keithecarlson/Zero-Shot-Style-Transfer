import os
import multiprocessing
import sys
import subprocess





def tokenizeFile(scriptDir,input_file_path,output_file_path,subWordList):
	
	return subprocess.call(['python',os.path.join(scriptDir,'subword-nmt-master','apply_bpe.py'),'-c', subWordList, '--input', input_file_path,'--output',output_file_path], shell=False)

 
if __name__ == '__main__': 

	pathToSubwordNMT = sys.argv[1]
	inputDir = sys.argv[2]
	outputDir = sys.argv[3]
	subWordList = sys.argv[4]

	
	threadCount = 3
	pool = multiprocessing.Pool(processes=threadCount)



	for root, subdirs, files in os.walk(inputDir):
		for subdir in subdirs:
			dir_path = os.path.join(root, subdir).replace(inputDir,outputDir)
			if not os.path.exists(dir_path):
				os.mkdir(dir_path)
		for file in files:

			input_file_path = os.path.join(root, file)
			output_file_path = os.path.join(root, file).replace(inputDir,outputDir)
			if not os.path.exists(output_file_path):
				r = pool.apply_async(tokenizeFile, args = (pathToSubwordNMT,input_file_path,output_file_path,subWordList))  
				
				
	pool.close()
	pool.join()

   

			