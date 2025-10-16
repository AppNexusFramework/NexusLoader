# test.py
from NexusFramework import NexusModuleManager

mm = NexusModuleManager(verbose=True)

# Load the module
test_module = mm.load_module("TestModule")

# Use classes from the module
TestClass = test_module.TestClass
instance = TestClass()

# Or get class directly
TestClass = mm.get_class("TestModule", "TestClass")
instance = TestClass()
instance.func1(10, "example")
instance.func2([1, 2, 3])
instance.func3({"key": "value"})