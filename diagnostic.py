#!/usr/bin/env python3
"""
Binary Module Diagnostic Tool
Helps diagnose and fix issues with compiled Python modules
"""

import sys
import os
import importlib.util
from pathlib import Path
import json
import subprocess
import platform


def check_python_version():
    """Check Python version"""
    print("="*70)
    print("PYTHON ENVIRONMENT")
    print("="*70)
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()}")
    print()


def check_module_file(pyd_file: Path):
    """Analyze a .pyd/.so file"""
    print("="*70)
    print(f"ANALYZING: {pyd_file.name}")
    print("="*70)
    print(f"File Path: {pyd_file}")
    print(f"File Size: {pyd_file.stat().st_size / 1024:.2f} KB")
    print(f"Exists: {pyd_file.exists()}")
    print()
    
    # Check for metadata files
    base_name = pyd_file.stem.split('.')[0]
    bin_dir = pyd_file.parent
    
    print("Metadata Files:")
    metadata_files = {
        'CLI API': bin_dir / f"{base_name}.nexus.cli",
        'REST API': bin_dir / f"{base_name}.nexus.rest",
        'Requirements': bin_dir / f"{base_name}.nexus.requirements",
        'Dependencies': bin_dir / f"{base_name}.nexus.dependencies",
        'Documentation': bin_dir / f"{base_name}.nexus.md",
    }
    
    for name, file in metadata_files.items():
        status = "✓ Found" if file.exists() else "✗ Missing"
        print(f"  {name}: {status}")
        
        if file.exists() and name == 'Requirements':
            try:
                with open(file, 'r') as f:
                    reqs = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    if reqs:
                        print(f"    Requirements found: {', '.join(reqs)}")
            except:
                pass
    
    print()


def test_direct_import(pyd_file: Path):
    """Try to import the module directly and catch detailed errors"""
    print("="*70)
    print("ATTEMPTING DIRECT IMPORT")
    print("="*70)
    
    module_name = pyd_file.stem.split('.')[0]
    
    # Add directory to path
    bin_dir = str(pyd_file.parent.absolute())
    if bin_dir not in sys.path:
        sys.path.insert(0, bin_dir)
    
    # Add to PATH for DLL search
    os.environ['PATH'] = bin_dir + os.pathsep + os.environ.get('PATH', '')
    
    # Try Windows DLL directory
    if platform.system() == 'Windows' and hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(bin_dir)
            print(f"✓ Added DLL directory: {bin_dir}")
        except Exception as e:
            print(f"⚠ Could not add DLL directory: {e}")
    
    print(f"\nTrying to import: {module_name}")
    print(f"From file: {pyd_file}\n")
    
    try:
        spec = importlib.util.spec_from_file_location(module_name, str(pyd_file))
        if spec is None or spec.loader is None:
            print("✗ FAILED: Could not create module spec")
            return None
        
        print("✓ Module spec created successfully")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        
        print("✓ Module object created successfully")
        print("\n🔄 Executing module (loading dependencies)...\n")
        
        spec.loader.exec_module(module)
        
        print("✓ SUCCESS! Module loaded successfully")
        print()
        
        # List what's in the module
        print("Module Contents:")
        classes = []
        functions = []
        other = []
        
        for name in dir(module):
            if name.startswith('_'):
                continue
            
            try:
                obj = getattr(module, name)
                if isinstance(obj, type):
                    classes.append(name)
                elif callable(obj):
                    functions.append(name)
                else:
                    other.append(name)
            except:
                pass
        
        if classes:
            print(f"  Classes ({len(classes)}):")
            for cls in classes:
                print(f"    • {cls}")
        
        if functions:
            print(f"  Functions ({len(functions)}):")
            for func in functions[:5]:
                print(f"    • {func}")
            if len(functions) > 5:
                print(f"    ... and {len(functions) - 5} more")
        
        if other:
            print(f"  Other attributes ({len(other)}):")
            for attr in other[:3]:
                print(f"    • {attr}")
        
        return module
        
    except ImportError as e:
        print(f"✗ IMPORT ERROR: {e}")
        print()
        
        error_str = str(e).lower()
        
        if "dll load failed" in error_str or "specified module could not be found" in error_str:
            print("🔍 This is a DLL dependency issue\n")
            print("Possible causes:")
            print("  1. Missing Python dependencies (packages not installed)")
            print("  2. Missing system DLLs (Visual C++ Runtime)")
            print("  3. Module compiled with different Python packages")
            print()
            print("💡 Solutions:")
            print("  1. Check and install all requirements:")
            
            req_file = pyd_file.parent / f"{module_name}.nexus.requirements"
            if req_file.exists():
                print(f"     pip install -r {req_file}")
            
            deps_file = pyd_file.parent / f"{module_name}.nexus.dependencies"
            if deps_file.exists():
                try:
                    with open(deps_file, 'r') as f:
                        deps = json.load(f)
                        if deps:
                            print(f"     pip install {' '.join(deps)}")
                except:
                    pass
            
            print()
            print("  2. Check that all dependencies are installed:")
            print("     pip list")
            print()
            print("  3. Try reinstalling the module's dependencies")
            
        elif "no module named" in error_str:
            missing_module = error_str.split("no module named")[1].strip().strip("'\"")
            print(f"🔍 Missing Python package: {missing_module}\n")
            print("💡 Solution:")
            print(f"   pip install {missing_module}")
        
        else:
            print("🔍 Unknown import error\n")
            print("Try:")
            print("  1. Reinstall all dependencies")
            print("  2. Check Python version compatibility")
            print("  3. Rebuild the module with correct environment")
        
        return None
        
    except Exception as e:
        print(f"✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        print()
        print("Full traceback:")
        traceback.print_exc()
        return None


def check_installed_packages():
    """Check what packages are installed"""
    print("\n" + "="*70)
    print("INSTALLED PACKAGES")
    print("="*70)
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        lines = result.stdout.split('\n')
        print("Installed packages:")
        for line in lines[:20]:
            print(f"  {line}")
        
        if len(lines) > 20:
            print(f"  ... and {len(lines) - 20} more packages")
        
    except Exception as e:
        print(f"Could not list packages: {e}")


def suggest_fixes(module_name: str, bin_dir: Path):
    """Suggest fixes based on available metadata"""
    print("\n" + "="*70)
    print("SUGGESTED FIXES")
    print("="*70)
    
    fixes = []
    
    # Check requirements file
    req_file = bin_dir / f"{module_name}.nexus.requirements"
    if req_file.exists():
        fixes.append(f"1. Install requirements: pip install -r {req_file}")
    
    # Check dependencies file
    deps_file = bin_dir / f"{module_name}.nexus.dependencies"
    if deps_file.exists():
        try:
            with open(deps_file, 'r') as f:
                deps = json.load(f)
                if deps:
                    fixes.append(f"2. Install dependencies: pip install {' '.join(deps)}")
        except:
            pass
    
    # Check if module might need rebuilding
    fixes.append("3. Verify Python version matches the compiled module")
    fixes.append(f"   Current: Python {sys.version_info.major}.{sys.version_info.minor}")
    fixes.append(f"   Module: {module_name} (check filename for python version)")
    
    # General suggestions
    fixes.append("4. Try reinstalling nexusframework:")
    fixes.append("   pip uninstall nexusframework -y")
    fixes.append("   pip install nexusframework")
    
    fixes.append("5. Check if source files exist alongside binaries")
    fixes.append(f"   Look in: {bin_dir}")
    
    for fix in fixes:
        print(fix)


def main():
    """Main diagnostic routine"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Binary Module Diagnostic Tool")
    parser.add_argument('module_file', nargs='?', help='Path to .pyd or .so file')
    parser.add_argument('--bin-dir', help='Binary directory to scan', 
                       default=str(Path.home() / '.nexus' / 'bin'))
    parser.add_argument('--list-packages', action='store_true', 
                       help='List installed packages')
    
    args = parser.parse_args()
    
    check_python_version()
    
    # Determine what to analyze
    if args.module_file:
        pyd_file = Path(args.module_file)
    else:
        # Scan bin directory
        bin_dir = Path(args.bin_dir)
        if not bin_dir.exists():
            print(f"Error: Directory not found: {bin_dir}")
            return
        
        # Find .pyd or .so files
        pyd_files = list(bin_dir.glob('*.pyd')) + list(bin_dir.glob('*.so'))
        
        if not pyd_files:
            print(f"No .pyd or .so files found in: {bin_dir}")
            return
        
        print(f"Found {len(pyd_files)} binary module(s) in {bin_dir}:")
        for f in pyd_files:
            print(f"  - {f.name}")
        print()
        
        # Use first one
        pyd_file = pyd_files[0]
        print(f"Analyzing first file: {pyd_file.name}\n")
    
    if not pyd_file.exists():
        print(f"Error: File not found: {pyd_file}")
        return
    
    # Run diagnostics
    check_module_file(pyd_file)
    module = test_direct_import(pyd_file)
    
    if args.list_packages:
        check_installed_packages()
    
    # Suggest fixes if import failed
    if module is None:
        module_name = pyd_file.stem.split('.')[0]
        suggest_fixes(module_name, pyd_file.parent)
    else:
        print("\n" + "="*70)
        print("✓ MODULE LOADED SUCCESSFULLY!")
        print("="*70)
        print("\nYou can now use this module with NexusLoader or import it directly.")


if __name__ == '__main__':
    main()