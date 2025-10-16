from NexusFramework import NexusDecorators

def func_validator(licenses):
    print(f"Validator created with licenses: {licenses}")
    if licenses.contains("pro"):
        return True
    else:
        return False
            
class Test:
    """
    A dynamic module loader for .pyd (Windows) and .so (Linux/Unix) binary files.
    
    Args:
        bin_path: Path to the directory containing binary modules
        modules: Optional list of module names to load. If None, loads all modules.
    """
    
    def __init__(self):
        pass
    
    NexusDecorators.allow_cli
    def func1(self, var1: int, var2: str):
        print("func1 executed")
        pass

    NexusDecorators.allow_restapi
    def func2(self, list_var: list):
        print("func2 executed")
        pass

    NexusDecorators.allow_license(func_validator(["free", "pro"]))
    def func3(self, dict_var: dict):
        print("func3 executed")

