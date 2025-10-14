# NexusLoader

A dynamic Python module loader for binary extensions (`.pyd` and `.so` files).

## Overview

`NexusLoader` is a class that simplifies the loading and management of compiled Python binary modules. It automatically discovers and loads `.pyd` (Windows) or `.so` (Linux/Unix) files from a specified directory, providing an easy-to-use interface for accessing these modules.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Basic Usage - Load All Modules](#basic-usage---load-all-modules)
  - [Selective Module Loading](#selective-module-loading)
  - [Accessing Loaded Modules](#accessing-loaded-modules)
  - [Checking Module Availability](#checking-module-availability)
  - [Error Handling](#error-handling)
- [API Reference](#api-reference)
  - [Class: NexusLoader](#class-nexusloader)
  - [Constructor](#constructor)
  - [Methods](#methods)
  - [Properties](#properties)
  - [Magic Methods](#magic-methods)
- [Complete Example](#complete-example)
- [Directory Structure Example](#directory-structure-example)
- [Platform Compatibility](#platform-compatibility)
- [Error Messages](#error-messages)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Source Code](#source-code)
- [Contributing](#contributing)
- [License](#license)

## Features

- ✨ **Automatic Discovery**: Automatically finds all binary modules in a directory
- 🎯 **Selective Loading**: Load all modules or specify which ones to load
- 🖥️ **Cross-Platform**: Supports both `.pyd` (Windows) and `.so` (Unix/Linux) files
- 🛡️ **Error Handling**: Gracefully handles loading failures with informative messages
- 📦 **Easy Access**: Multiple ways to access loaded modules
- 🔍 **Module Management**: Track and query loaded modules
- 🚀 **Zero Dependencies**: Uses only Python standard library
- 💪 **Type Hints**: Full type annotation support

## Installation

Simply copy the `NexusLoader` class into your project. No additional dependencies required beyond Python's standard library.

### Requirements

- Python 3.6 or higher
- Standard library modules: `os`, `importlib`, `sys`, `pathlib`, `typing`

### Installation Methods

#### Method 1: Direct Copy

Copy the `nexus_loader.py` file into your project directory:

```
project/
├── nexus_loader.py
└── your_script.py
```

#### Method 2: As a Package

Create a package structure:

```
project/
├── nexus/
│   ├── __init__.py
│   └── loader.py
└── your_script.py
```

Then import:

```python
from nexus.loader import NexusLoader
```

## Quick Start

```python
from nexus_loader import NexusLoader

# Load all modules from a directory
loader = NexusLoader("/path/to/binary/modules")

# Access a loaded module
my_module = loader["module_name"]
my_module.some_function()

# List all loaded modules
print(loader.list_loaded_modules())
```

## Usage

### Basic Usage - Load All Modules

Load all `.pyd` and `.so` files from a directory:

```python
from nexus_loader import NexusLoader

# Load all modules from the directory
loader = NexusLoader("/path/to/binary/modules")

# List all loaded modules
print(f"Loaded modules: {loader.list_loaded_modules()}")

# Output: Loaded modules: ['module1', 'module2', 'module3']
```

### Selective Module Loading

Load only specific modules by providing a list of module names:

```python
# Load only specific modules
loader = NexusLoader(
    "/path/to/binary/modules",
    modules=["module1", "module2", "module3"]
)

# Check what was loaded
print(f"Successfully loaded: {loader.list_loaded_modules()}")
```

### Accessing Loaded Modules

There are multiple ways to access loaded modules:

#### Method 1: Dictionary-Style Access (Recommended)

```python
# Access module using dictionary syntax
module = loader["module_name"]
result = module.some_function()
```

#### Method 2: Using get_module()

```python
# Access module using get_module method
module = loader.get_module("module_name")
result = module.some_function()
```

#### Method 3: Direct Access

```python
# Direct access to the loaded_modules dictionary
module = loader.loaded_modules["module_name"]
result = module.some_function()
```

### Checking Module Availability

```python
# Check if a module is loaded using 'in' operator
if "module_name" in loader:
    print("Module is loaded and ready to use!")
    module = loader["module_name"]
else:
    print("Module not found")

# Get list of all loaded modules
available_modules = loader.list_loaded_modules()
print(f"Available modules: {available_modules}")

# Count loaded modules
print(f"Total modules loaded: {len(loader.list_loaded_modules())}")
```

### Error Handling

```python
from nexus_loader import NexusLoader

# Handle directory errors
try:
    loader = NexusLoader("/path/to/binary/modules")
except FileNotFoundError as e:
    print(f"Directory not found: {e}")
except NotADirectoryError as e:
    print(f"Path is not a directory: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")

# Handle module access errors
try:
    module = loader.get_module("nonexistent_module")
except KeyError as e:
    print(f"Module not found: {e}")
    print(f"Available modules: {loader.list_loaded_modules()}")
```

## API Reference

### Class: NexusLoader

The main class for loading and managing binary Python modules.

```python
class NexusLoader:
    """
    A dynamic module loader for .pyd (Windows) and .so (Linux/Unix) binary files.
    
    Args:
        bin_path: Path to the directory containing binary modules
        modules: Optional list of module names to load. If None, loads all modules.
    """
```

### Constructor

```python
NexusLoader(bin_path: str, modules: Optional[List[str]] = None)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bin_path` | `str` | Required | Path to the directory containing binary modules |
| `modules` | `Optional[List[str]]` | `None` | List of specific module names to load. If `None`, loads all modules |

**Raises:**

| Exception | Description |
|-----------|-------------|
| `FileNotFoundError` | If the bin_path doesn't exist or contains no binary modules |
| `NotADirectoryError` | If bin_path is not a directory |

**Example:**

```python
# Load all modules
loader = NexusLoader("/opt/app/modules")

# Load specific modules
loader = NexusLoader("/opt/app/modules", modules=["crypto", "network"])
```

### Methods

#### `get_module(name: str) -> Any`

Retrieve a loaded module by name.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the module to retrieve |

**Returns:**
- The loaded module object

**Raises:**
- `KeyError`: If the module was not loaded

**Example:**

```python
crypto_module = loader.get_module("crypto")
result = crypto_module.encrypt("data")
```

#### `list_loaded_modules() -> List[str]`

Get a list of all successfully loaded module names.

**Returns:**
- `List[str]`: List of module names

**Example:**

```python
modules = loader.list_loaded_modules()
print(f"Loaded modules: {modules}")
# Output: Loaded modules: ['crypto', 'network', 'database']
```

### Properties

#### `loaded_modules: Dict[str, Any]`

Dictionary containing all successfully loaded modules, keyed by module name.

**Type:** `Dict[str, Any]`

**Example:**

```python
# Access all loaded modules
for name, module in loader.loaded_modules.items():
    print(f"Module: {name}")
```

#### `bin_path: Path`

Path object representing the binary modules directory.

**Type:** `pathlib.Path`

**Example:**

```python
print(f"Loading from: {loader.bin_path}")
```

#### `modules_to_load: Optional[List[str]]`

List of specific modules to load, or `None` if loading all modules.

**Type:** `Optional[List[str]]`

**Example:**

```python
if loader.modules_to_load:
    print(f"Selective loading: {loader.modules_to_load}")
else:
    print("Loading all modules")
```

### Magic Methods

#### `__getitem__(name: str) -> Any`

Allows dictionary-style access to modules.

**Example:**

```python
module = loader["module_name"]
```

#### `__contains__(name: str) -> bool`

Check if a module is loaded using the `in` operator.

**Example:**

```python
if "crypto" in loader:
    print("Crypto module is loaded!")
```

#### `__repr__() -> str`

String representation of the loader.

**Example:**

```python
print(loader)
# Output: NexusLoader(bin_path='/opt/app/modules', loaded=5 modules)
```

## Complete Example

Here's a complete example demonstrating all features:

```python
from nexus_loader import NexusLoader
import sys

def main():
    """Complete example of NexusLoader usage."""
    
    # Configuration
    modules_path = "/opt/myapp/modules"
    required_modules = ["crypto", "network", "database"]
    
    try:
        # Initialize loader with specific modules
        print(f"Loading modules from: {modules_path}")
        loader = NexusLoader(modules_path, modules=required_modules)
        
        # Display loaded modules
        loaded = loader.list_loaded_modules()
        print(f"\n✓ Successfully loaded {len(loaded)} modules:")
        for module_name in loaded:
            print(f"  - {module_name}")
        
        # Check for missing modules
        missing = set(required_modules) - set(loaded)
        if missing:
            print(f"\n⚠ Warning: Missing modules: {missing}")
        
        # Use crypto module
        if "crypto" in loader:
            print("\n--- Using Crypto Module ---")
            crypto = loader["crypto"]
            encrypted = crypto.encrypt("Hello, World!")
            print(f"Encrypted data: {encrypted}")
            decrypted = crypto.decrypt(encrypted)
            print(f"Decrypted data: {decrypted}")
        
        # Use network module
        if "network" in loader:
            print("\n--- Using Network Module ---")
            network = loader.get_module("network")
            network.connect("192.168.1.1", port=8080)
            status = network.get_status()
            print(f"Connection status: {status}")
        
        # Use database module
        if "database" in loader:
            print("\n--- Using Database Module ---")
            db = loader["database"]
            db.connect("localhost", 5432, "mydb")
            result = db.query("SELECT * FROM users LIMIT 5")
            print(f"Query result: {result}")
        
        # Display loader info
        print(f"\n{loader}")
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except NotADirectoryError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"✗ Module error: {e}", file=sys.stderr)
        print(f"Available modules: {loader.list_loaded_modules()}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Directory Structure Example

### Basic Structure

```
/opt/myapp/
├── modules/              # Binary modules directory
│   ├── crypto.so        # Linux/Unix binary
│   ├── network.so       # Linux/Unix binary
│   ├── database.so      # Linux/Unix binary
│   └── utils.pyd        # Windows binary
├── main.py              # Your application
└── nexus_loader.py      # NexusLoader class
```

### Package Structure

```
myproject/
├── nexus/
│   ├── __init__.py
│   └── loader.py        # NexusLoader class
├── modules/
│   ├── crypto.so
│   ├── network.so
│   └── database.so
├── tests/
│   ├── __init__.py
│   └── test_loader.py
├── main.py
└── README.md
```

## Platform Compatibility

### Supported Platforms

| Platform | Extension | Notes |
|----------|-----------|-------|
| **Windows** | `.pyd` | Python extension modules for Windows |
| **Linux** | `.so` | Shared object files |
| **macOS** | `.so` | Shared object files |
| **Unix** | `.so` | Shared object files |

### File Extension Mapping

```python
# The loader automatically handles:
# - Windows: module_name.pyd
# - Linux/Unix/macOS: module_name.so
```

### Cross-Platform Usage

```python
# Same code works on all platforms
loader = NexusLoader("/path/to/modules")

# The loader automatically finds:
# - crypto.pyd on Windows
# - crypto.so on Linux/macOS
```

## Error Messages

### Common Error Messages

#### Directory Not Found

```
FileNotFoundError: Binary path does not exist: /path/to/modules
```

**Solution:** Verify the path exists and is spelled correctly.

#### Not a Directory

```
NotADirectoryError: Binary path is not a directory: /path/to/file
```

**Solution:** Ensure you're providing a path to a directory, not a file.

#### No Binary Modules Found

```
FileNotFoundError: No binary modules found in: /path/to/modules
```

**Solution:** Check that the directory contains `.pyd` or `.so` files.

#### Module Not Loaded

```
KeyError: Module 'module_name' not loaded. Available modules: ['module1', 'module2']
```

**Solution:** Check the module name spelling or verify it exists in the directory.

#### Module Loading Failed

```
Failed to load module crypto: [error details]
```

**Solution:** Check module dependencies and compatibility.

#### Missing Requested Modules

```
Warning: Could not load requested modules: {'module1', 'module2'}
```

**Solution:** Verify the modules exist in the directory and are compatible.

## Best Practices

### 1. Always Validate Paths

```python
import os

modules_path = "/path/to/modules"
if os.path.exists(modules_path) and os.path.isdir(modules_path):
    loader = NexusLoader(modules_path)
else:
    print(f"Invalid path: {modules_path}")
```

### 2. Use Selective Loading for Performance

```python
# Only load what you need
loader = NexusLoader(
    "/path/to/modules",
    modules=["crypto", "network"]  # Don't load unused modules
)
```

### 3. Check Module Availability Before Use

```python
# Always check before using
if "crypto" in loader:
    crypto = loader["crypto"]
    crypto.some_function()
else:
    print("Crypto module not available")
```

### 4. Handle Errors Gracefully

```python
try:
    loader = NexusLoader("/path/to/modules")
    module = loader["my_module"]
except (FileNotFoundError, KeyError) as e:
    print(f"Error: {e}")
    # Provide fallback or exit gracefully
```

### 5. Use Type Hints

```python
from typing import Optional, List
from nexus_loader import NexusLoader

def initialize_loader(path: str, modules: Optional[List[str]] = None) -> NexusLoader:
    """Initialize and return a configured NexusLoader."""
    return NexusLoader(path, modules)
```

### 6. Log Module Loading

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

loader = NexusLoader("/path/to/modules")
logger.info(f"Loaded modules: {loader.list_loaded_modules()}")
```

### 7. Use Context Managers for Resources

If your loaded modules have resources that need cleanup:

```python
class ManagedNexusLoader:
    def __init__(self, path, modules=None):
        self.loader = NexusLoader(path, modules)
    
    def __enter__(self):
        return self.loader
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup loaded modules if needed
        for module in self.loader.loaded_modules.values():
            if hasattr(module, 'cleanup'):
                module.cleanup()

# Usage
with ManagedNexusLoader("/path/to/modules") as loader:
    module = loader["my_module"]
    module.do_work()
```

## Troubleshooting

### Module Won't Load

**Problem:** Module fails to load with import error.

**Solutions:**

1. Check Python version compatibility
2. Verify module dependencies are installed
3. Ensure module is compiled for your platform
4. Check file permissions

```python
import sys
print(f"Python version: {sys.version}")
print(f"Platform: {sys.platform}")
```

### Import Error: Undefined Symbol

**Problem:** Module loads but has missing dependencies.

**Solutions:**

1. Install required system libraries
2. Check LD_LIBRARY_PATH (Linux) or PATH (Windows)
3. Verify module was compiled correctly

```bash
# Linux: Check dependencies
ldd /path/to/module.so

# macOS: Check dependencies
otool -L /path/to/module.so
```

### Performance Issues

**Problem:** Loading takes too long.

**Solutions:**

1. Use selective loading for only required modules
2. Load modules lazily when needed
3. Cache the loader instance

```python
# Lazy loading pattern
class LazyLoader:
    def __init__(self, path):
        self.path = path
        self._loader = None
    
    @property
    def loader(self):
        if self._loader is None:
            self._loader = NexusLoader(self.path)
        return self._loader
```

### Module Conflicts

**Problem:** Module names conflict with Python builtins.

**Solutions:**

1. Rename binary files to avoid conflicts
2. Use namespacing in your code
3. Access via loader explicitly

```python
# Don't do this if 'json' is a binary module
import json  # This imports Python's built-in

# Do this instead
loader = NexusLoader("/path/to/modules")
custom_json = loader["json"]  # Your binary module
```

## Source Code

Here's the complete source code for `NexusLoader`:

```python
import os
import importlib.util
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

