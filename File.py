import os
import shutil
import time
import hashlib
import pathlib


# 2020年8月4日16:52:56
class File:
	def __init__(self, filePath):
		if not isinstance(filePath, str):
			raise TypeError(f"the file path must be a string, instead of '{filePath}' {type(filePath)}")
		
		if os.path.isabs(filePath):
			self.absPath = os.path.abspath(filePath).replace("\\", "/")
		else:
			self.absPath = os.path.abspath(os.path.join(os.getcwd(), filePath)).replace("\\", "/")
	
	@property
	def isDirectory(self):
		return os.path.isdir(self.absPath)
	
	@property
	def isFile(self):
		return os.path.isfile(self.absPath)
	
	@property
	def isLink(self):
		return os.path.islink(self.absPath)
	
	@property
	def exists(self):
		return os.path.exists(self.absPath)
	
	def rename(self, newName):
		os.rename(self.path, self.parent.child(newName).path)
	
	def mkdirs(self):
		if not self.exists:
			os.makedirs(self.path)
	
	def touch(self, content=None):
		if not self.exists:
			if content is not None:
				with open(self.path, "w+", encoding="utf-8") as f:
					f.write(content)
			else:
				pathlib.Path(self.path).touch()
	
	@property
	def content(self):
		if not self.exists:
			raise FileNotFoundError(f"'{self.absPath}' is not found")
		
		if self.isDirectory:
			raise IsADirectoryError(f"'{self.absPath}' is not a file")
		
		with open(self.path, "r", encoding="utf-8") as f:
			return f.read()
	
	def put(self, content):
		if self.exists and self.isDirectory:
			raise IsADirectoryError(f"'{self.absPath}' is not a file")
		
		with open(self.path, "w+", encoding="utf-8") as f:
			f.write(content)
	
	def makeParentDirs(self):
		if not self.parent.exists:
			os.makedirs(self.parent.path)
	
	@property
	def name(self):
		return os.path.basename(self.absPath)
	
	@property
	def length(self):
		if not self.exists:
			raise FileNotFoundError(f"'{self.absPath}' is not found")
		
		if not self.isFile:
			raise IsADirectoryError(f"'{self.absPath}' is not a file")
		
		return os.path.getsize(self.absPath)
	
	@property
	def files(self):
		if not self.exists:
			raise FileNotFoundError(f"'{self.absPath}' is not found")
		
		if self.isFile:
			raise NotADirectoryError(f"'{self.absPath}' is not a Directory")
		
		fileList = []
		
		for f in os.listdir(self.path):
			fileList.append(File(os.path.join(self.path, f)))
		
		return fileList
	
	@property
	def isDirty(self):
		if not self.exists:
			raise FileNotFoundError(f"'{self.absPath}' is not found")
		
		if self.isFile:
			raise NotADirectoryError(f"'{self.absPath}' is not a Directory")
		
		return len(self.files) > 0
	
	def clear(self):
		if not self.exists:
			return
		
		if self.isFile:
			raise NotADirectoryError(f"'{self.absPath}' is not a Directory")
		
		for pf in self.files:
			pf.delete()
	
	@property
	def path(self):
		return self.absPath.replace("\\", "/")
	
	def relPath(self, baseDir=None):
		if baseDir is None:
			return os.path.relpath(self.path).replace("\\", "/")
		
		bd = baseDir if isinstance(baseDir, File) else File(baseDir)
		if bd.isDirectory:
			return os.path.relpath(self.path, bd.path).replace("\\", "/")
		return self.path
	
	def append(self, relPath):
		return File(os.path.join(self.path, relPath))
	
	@property
	def parent(self):
		return File(os.path.dirname(self.absPath))
	
	def delete(self):
		if self.exists:
			if self.isFile:
				os.remove(self.absPath)
			
			if self.isDirectory:
				shutil.rmtree(self.absPath)
	
	def child(self, childName):
		return File(os.path.join(self.absPath, childName))
	
	def hasChild(self, childName):
		return os.path.exists(self.child(childName).path)
	
	@property
	def sha1(self):
		if not self.exists:
			raise FileNotFoundError(f"'{self.absPath}' is not found")
		
		if self.isDirectory:
			raise IsADirectoryError(f"'{self.absPath}' is not a file")
		
		with open(self.absPath, 'rb') as f:
			sha1obj = hashlib.sha1()
			sha1obj.update(f.read())
			sha1 = sha1obj.hexdigest()
			return sha1
	
	@property
	def createdTime(self):
		return int(os.path.getctime(self.absPath))
	
	@property
	def modifiedTime(self):
		return int(os.path.getmtime(self.absPath))
	
	def getCreatedTimeByFormat(self, format="%Y-%m-%d %H:%M:%S"):
		return time.strftime(format, time.localtime(self.createdTime))
	
	def getModifiedTimeByFormat(self, format="%Y-%m-%d %H:%M:%S"):
		return time.strftime(format, time.localtime(self.modifiedTime))
	
	class Iter:
		def __init__(self, object):
			self.object = object
			self.files = object.files
			self.index = 0
			self.end = self.files.__len__()
		
		def __next__(self):
			if self.index < self.end:
				ret = self.files[self.index]
				self.index += 1
				return ret
			else:
				raise StopIteration
	
	def __contains__(self, item):
		return self.hasChild(item)
	
	def __getitem__(self, key):
		if not isinstance(key, str):
			raise TypeError(f"The key must be a string, instead of '{key}' {type(key)}")
		
		if self.hasChild(key):
			return self.child(key)
		else:
			return None
	
	def __len__(self):
		return len(self.files)
	
	def __iter__(self):
		return self.Iter(self)
	
	def __repr__(self):
		return self.name
