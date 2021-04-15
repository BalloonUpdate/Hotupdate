import sys
import os
import time

productName = 'UpdaterHotupdatePackage'
productVersion = time.strftime('%y-%m-%d_%H-%M-%S') if 'tag_name' not in os.environ else os.environ['tag_name']


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
