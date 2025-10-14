import os
import importlib.util
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any


class NexusLoader:
    """
    A dynamic module loader for .pyd (Windows) and .so (Linux/Unix) binary files.
    
    Args:
        bin_path: Path to the directory containing binary modules
        modules: Optional list of module names to load. If None, loads all modules.
    """
    
    def __init__(self, bin_path: str, modules: Optional[List[str]] = None):
        self.bin_path = Path(bin_path)
        self.modules_to_load = modules
        self.loaded_modules: Dict[str, Any] = {}
        
        # Validate bin_path exists
        if not self.bin_path.exists():
            raise FileNotFoundError(f"Binary path does not exist: {bin_path}")
        
        if not self.bin_path.is_dir():
            raise NotADirectoryError(f"Binary path is not a directory: {bin_path}")
        
        # Load modules during initialization
        self._load_modules()
    
    def _get_binary_files(self) -> List[Path]:
        """Get all .pyd and .so files from the bin_path directory."""
        binary_extensions = ['.pyd', '.so']
        binary_files = []
        
        for ext in binary_extensions:
            binary_files.extend(self.bin_path.glob(f'*{ext}'))
        
        return binary_files
    
    def _extract_module_name(self, file_path: Path) -> str:
        """Extract module name from file path (without extension)."""
        return file_path.stem
    
    def _load_module(self, file_path: Path) -> Any:
        """
        Load a single binary module from file path.
        
        Args:
            file_path: Path to the binary module file
            
        Returns:
            The loaded module object
        """
        module_name = self._extract_module_name(file_path)
        
        # Create module spec
        spec = importlib.util.spec_from_file_location(module_name, str(file_path))
        
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module spec for: {file_path}")
        
        # Create module from spec
        module = importlib.util.module_from_spec(spec)
        
        # Add to sys.modules to make it importable
        sys.modules[module_name] = module
        
        # Execute the module
        spec.loader.exec_module(module)
        
        return module
    
    def _load_modules(self) -> None:
        """Load all specified modules or all available modules."""
        binary_files = self._get_binary_files()
        
        if not binary_files:
            raise FileNotFoundError(f"No binary modules found in: {self.bin_path}")
        
        for file_path in binary_files:
            module_name = self._extract_module_name(file_path)
            
            # Skip if specific modules requested and this isn't one of them
            if self.modules_to_load is not None and module_name not in self.modules_to_load:
                continue
            
            try:
                module = self._load_module(file_path)
                self.loaded_modules[module_name] = module
                print(f"Successfully loaded module: {module_name}")
            except Exception as e:
                print(f"Failed to load module {module_name}: {e}")
        
        # Check if all requested modules were loaded
        if self.modules_to_load is not None:
            loaded_names = set(self.loaded_modules.keys())
            requested_names = set(self.modules_to_load)
            missing = requested_names - loaded_names
            
            if missing:
                print(f"Warning: Could not load requested modules: {missing}")
    
    def get_module(self, name: str) -> Any:
        """
        Get a loaded module by name.
        
        Args:
            name: Name of the module to retrieve
            
        Returns:
            The loaded module object
            
        Raises:
            KeyError: If module was not loaded
        """
        if name not in self.loaded_modules:
            raise KeyError(f"Module '{name}' not loaded. Available modules: {list(self.loaded_modules.keys())}")
        
        return self.loaded_modules[name]
    
    def list_loaded_modules(self) -> List[str]:
        """Return a list of all loaded module names."""
        return list(self.loaded_modules.keys())
    
    def __getitem__(self, name: str) -> Any:
        """Allow dictionary-style access to modules."""
        return self.get_module(name)
    
    def __contains__(self, name: str) -> bool:
        """Check if a module is loaded."""
        return name in self.loaded_modules
    
    def __repr__(self) -> str:
        return f"NexusLoader(bin_path='{self.bin_path}', loaded={len(self.loaded_modules)} modules)"
