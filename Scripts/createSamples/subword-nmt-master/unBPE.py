import string

inFile = open('tokenizedSimple.tok','r')
outFile=open('unDifferentToke.txt','w')

text = inFile.read()
outFile.write(string.replace(text,'@@ ',''))