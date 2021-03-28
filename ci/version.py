import sys
import os

productName = 'UpdaterHotupdatePackage'
productVersion = '2.6.4'

if 'tag_name' in os.environ:
    productVersion = os.environ['tag_name']


if __name__ == "__main__":
    if len(sys.argv) > 1:
        param = sys.argv[1]

        if param == 'version':
            print(productVersion)
        elif param == 'name':
            print(productName)
        elif param == 'both':
            print(productName + '-' + productVersion)
        else:
            print('available value: version, name, both')
