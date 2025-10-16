# test.py
from NexusFramework import ModuleManager

mm = ModuleManager(verbose=True)

# Load the module
test_module = mm.load_module("TestModule")

# Use classes from the module
TestClass = test_module.TestClass
instance = TestClass()

# Or get class directly
TestClass = mm.get_class("TestModule", "TestClass")
instance = TestClass()