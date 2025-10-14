# NexusLoader

A dynamic Python module loader for binary extensions (`.pyd` and `.so` files).

## Quick Start

```python
from NexusLoader import NexusLoader

# Load all modules from current directory
loader = NexusLoader(".")

# Access a loaded module
my_module = loader["module_name"]
my_module.some_function()

# List all loaded modules
print(loader.list_loaded_modules())
```

## Usage Examples

### Load All Modules

```python
# Load all binary modules from a directory
loader = NexusLoader("/path/to/binary/modules")

# List what was loaded
print(f"Loaded modules: {loader.list_loaded_modules()}")
```

### Load Specific Modules

```python
# Load only specific modules
loader = NexusLoader(
    "/path/to/binary/modules",
    modules=["module1", "module2"]
)
```

### Access Modules

```python
# Method 1: Dictionary-style (recommended)
module = loader["module_name"]

# Method 2: Using get_module()
module = loader.get_module("module_name")

# Method 3: Direct access
module = loader.loaded_modules["module_name"]
```

### Check Module Availability

```python
# Check if module is loaded
if "module_name" in loader:
    print("Module is available!")
    module = loader["module_name"]

# List all available modules
available = loader.list_loaded_modules()
print(f"Available: {available}")
```

## API Reference

### Constructor

```python
NexusLoader(bin_path: str, modules: Optional[List[str]] = None)
```

**Parameters:**
- `bin_path` (str): Path to directory containing binary modules
- `modules` (Optional[List[str]]): Specific modules to load. If None, loads all.

**Raises:**
- `FileNotFoundError`: If bin_path doesn't exist or has no binary modules
- `NotADirectoryError`: If bin_path is not a directory

### Methods

#### `get_module(name: str) -> Any`
Retrieve a loaded module by name.

#### `list_loaded_modules() -> List[str]`
Get list of all loaded module names.

### Magic Methods

- `loader["module_name"]` - Dictionary-style access
- `"module_name" in loader` - Check if module is loaded
- `str(loader)` - String representation

## Error Handling

```python
try:
    loader = NexusLoader("/path/to/modules")
    module = loader["my_module"]
except FileNotFoundError as e:
    print(f"Directory error: {e}")
except KeyError as e:
    print(f"Module not found: {e}")
    print(f"Available: {loader.list_loaded_modules()}")
```

## Platform Compatibility

| Platform | Extension | Notes |
|----------|-----------|-------|
| Windows | `.pyd` | Python extension modules |
| Linux | `.so` | Shared object files |
| macOS | `.so` | Shared object files |

## Best Practices

1. **Validate paths before loading**
2. **Use selective loading** for better performance
3. **Check module availability** before use
4. **Handle errors gracefully**
5. **Use type hints** in your code

## Complete Example

```python
from NexusLoader import NexusLoader
import sys

def main():
    try:
        # Load specific modules
        loader = NexusLoader(
            "./bin",
            modules=["crypto", "network"]
        )
        
        # Check what loaded
        print(f"Loaded: {loader.list_loaded_modules()}")
        
        # Use modules
        if "crypto" in loader:
            crypto = loader["crypto"]
            result = crypto.encrypt("Hello")
            print(f"Encrypted: {result}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Troubleshooting

### Module Won't Load
- Check Python version compatibility
- Verify dependencies are installed
- Ensure module compiled for your platform

### ImportError
- Install missing dependencies
- Check module is in correct directory
- Verify file permissions

For more information, see the full documentation in the repository.
