

import os
import sys
import ctypes

# Add your DLL directory before importing
os.add_dll_directory(r"C:\Users\Software Engineering\.nexus\bin")

# Print diagnostic info
print("sys.path:")
for p in sys.path:
    print("  ", p)

print("\nPATH:")
for p in os.environ["PATH"].split(";"):
    print("  ", p)



# ✅ Correct import syntax
from NexusFramework.NexusLoader import NexusLoader

# Initialize the loader
loader = NexusLoader(r"C:\Users\Software Engineering\.nexus\bin", verbose=True)

# Print loaded modules info
print(loader.loaded_modules)
