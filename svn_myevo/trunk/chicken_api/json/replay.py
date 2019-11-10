import requests
import sys


def getFileContent(pathAndFileName):
    with open(pathAndFileName, 'r') as theFile:
        data = theFile.read()
        return data

def main():
	URL = "http://localhost:5202/chicken/api/order/create"

	data = getFileContent(sys.argv[1])
	r = requests.post(url=URL, data=data)

	print r.text

if __name__ == '__main__':
	main()
