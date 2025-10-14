"""
Complete Module Manager - All-in-One Solution
Handles discovery, conflict resolution, inspection, and execution of compiled Python modules

Author: Nexus Team
Version: 1.0.0
License: MIT
"""

import os
import sys
import glob
import inspect
import shutil
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


class ModuleManager:
    """Complete module management: discovery, conflicts, inspection, and execution."""
    
    def __init__(self, search_path: Optional[str] = None, auto_fix_conflicts: bool = False):
        """
        Initialize the Module Manager.
        
        Args:
            search_path: Directory to search for modules. Defaults to current directory.
            auto_fix_conflicts: Automatically fix .py/.pyd conflicts without asking
        """
        self.search_path = search_path or os.getcwd()
        self.modules = {}
        self.module_files = []
        self.auto_fix_conflicts = auto_fix_conflicts
        self.conflicts_found = []
        
        # Add search path to sys.path
        if self.search_path not in sys.path:
            sys.path.insert(0, self.search_path)
    
    # ========================================================================
    # CONFLICT RESOLUTION
    # ========================================================================
    
    def find_conflicts(self) -> tuple:
        """Find .py files that conflict with .pyd/.so files."""
        conflicts = []
        
        # Find all compiled modules
        current_dir = os.getcwd()
        os.chdir(self.search_path)
        pyd_files = glob.glob("*.pyd")
        so_files = glob.glob("*.so")
        os.chdir(current_dir)
        
        compiled_modules = set()
        for f in pyd_files + so_files:
            # Extract module name (e.g., NexusLicense from NexusLicense.cp311-win_amd64.pyd)
            name = f.split('.')[0]
            compiled_modules.add(name)
        
        # Check for .py files with same names
        for module_name in compiled_modules:
            py_file = os.path.join(self.search_path, f"{module_name}.py")
            if os.path.exists(py_file):
                conflicts.append(py_file)
        
        self.conflicts_found = conflicts
        return conflicts, compiled_modules
    
    def backup_file(self, filepath: str) -> str:
        """Create a timestamped backup of a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{filepath}.{timestamp}.bak"
        shutil.copy2(filepath, backup_path)
        return backup_path
    
    def resolve_conflicts(self, method: str = 'rename') -> bool:
        """
        Resolve conflicts between .py and .pyd/.so files.
        
        Args:
            method: 'rename' (to .bak), 'delete', 'move', or 'ask'
            
        Returns:
            True if conflicts were resolved
        """
        conflicts, compiled_modules = self.find_conflicts()
        
        if not conflicts:
            return True
        
        print(f"\n⚠️  Found {len(conflicts)} conflicting .py file(s):")
        for f in conflicts:
            size = os.path.getsize(f)
            print(f"  - {f} ({size} bytes)")
        
        if method == 'ask':
            print("\n" + "="*70)
            print("SOLUTIONS:")
            print("="*70)
            print("1. Rename .py files to .py.bak (keeps backup)")
            print("2. Delete .py files permanently (creates backup)")
            print("3. Move .py files to 'source_backup' folder")
            print("4. Skip (manual fix required)")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == '1':
                method = 'rename'
            elif choice == '2':
                method = 'delete'
            elif choice == '3':
                method = 'move'
            else:
                print("\n⚠️  Skipping conflict resolution")
                return False
        
        # Execute the selected method
        if method == 'rename':
            print("\nRenaming files to .py.bak...")
            for f in conflicts:
                new_name = f + '.bak'
                os.rename(f, new_name)
                print(f"  ✓ {f} → {new_name}")
            print("\n✓ All files renamed!")
            
        elif method == 'delete':
            print("\nDeleting files (creating backups)...")
            for f in conflicts:
                backup = self.backup_file(f)
                print(f"  📦 Backup: {backup}")
                os.remove(f)
                print(f"  ✓ Deleted: {f}")
            print("\n✓ All files deleted! (backups created)")
            
        elif method == 'move':
            backup_dir = os.path.join(self.search_path, 'source_backup')
            os.makedirs(backup_dir, exist_ok=True)
            
            print(f"\nMoving files to {backup_dir}/...")
            for f in conflicts:
                dest = os.path.join(backup_dir, os.path.basename(f))
                shutil.move(f, dest)
                print(f"  ✓ {f} → {dest}")
            print(f"\n✓ All files moved to {backup_dir}/")
        
        # Verify resolution
        remaining, _ = self.find_conflicts()
        if remaining:
            print(f"\n⚠️  Still {len(remaining)} conflict(s) remaining!")
            return False
        else:
            print("\n✓ All conflicts resolved!")
            return True
    
    # ========================================================================
    # MODULE DISCOVERY
    # ========================================================================
    
    def find_module_files(self) -> List[str]:
        """Find all .pyd and .so files in the search path."""
        current_dir = os.getcwd()
        os.chdir(self.search_path)
        
        pyd_files = glob.glob("*.pyd")
        so_files = glob.glob("*.so")
        
        os.chdir(current_dir)
        
        self.module_files = pyd_files + so_files
        
        # Check for conflicts
        if self.module_files:
            conflicts, _ = self.find_conflicts()
            if conflicts:
                if self.auto_fix_conflicts:
                    self.resolve_conflicts(method='rename')
                else:
                    print("\n⚠️  Conflicts detected. Run resolve_conflicts() to fix.")
        
        return self.module_files
    
    def extract_module_name(self, filename: str) -> str:
        """Extract the Python module name from a .pyd/.so file."""
        name = filename.rsplit('.', 1)[0]
        
        # For files like: NexusLicense.cp311-win_amd64.pyd
        if '.cp' in name or '.cpython' in name:
            name = name.split('.')[0]
        
        return name
    
    def load_module(self, module_name: str) -> Optional[Any]:
        """Load a module by name."""
        try:
            module = __import__(module_name)
            self.modules[module_name] = module
            return module
        except ImportError as e:
            print(f"Failed to import {module_name}: {e}")
            return None
        except Exception as e:
            print(f"Error loading {module_name}: {type(e).__name__}: {e}")
            return None
    
    # ========================================================================
    # MODULE INSPECTION
    # ========================================================================
    
    def get_module_info(self, module: Any) -> Dict[str, Any]:
        """Get detailed information about a module."""
        info = {
            'name': module.__name__,
            'file': getattr(module, '__file__', 'unknown'),
            'doc': module.__doc__,
            'classes': [],
            'functions': [],
            'attributes': []
        }
        
        for name in dir(module):
            if name.startswith('_'):
                continue
            
            try:
                obj = getattr(module, name)
                
                if inspect.isclass(obj):
                    info['classes'].append({
                        'name': name,
                        'object': obj,
                        'methods': self._get_class_methods(obj),
                        'doc': obj.__doc__
                    })
                elif inspect.isfunction(obj) or inspect.isbuiltin(obj):
                    info['functions'].append({
                        'name': name,
                        'object': obj,
                        'doc': obj.__doc__
                    })
                else:
                    info['attributes'].append({
                        'name': name,
                        'type': type(obj).__name__,
                        'value': str(obj) if not callable(obj) else 'callable'
                    })
            except Exception as e:
                pass  # Skip problematic attributes
        
        return info
    
    def _get_class_methods(self, cls: type) -> List[Dict[str, Any]]:
        """Get all methods from a class with parameter information."""
        methods = []
        
        for name in dir(cls):
            if name.startswith('_'):
                continue
            
            try:
                method = getattr(cls, name)
                if callable(method):
                    # Get parameter information
                    params = self._get_method_parameters(method)
                    
                    methods.append({
                        'name': name,
                        'object': method,
                        'doc': method.__doc__,
                        'is_static': isinstance(inspect.getattr_static(cls, name), staticmethod),
                        'is_class': isinstance(inspect.getattr_static(cls, name), classmethod),
                        'parameters': params['parameters'],
                        'return_type': params['return_type'],
                        'signature': params['signature']
                    })
            except Exception:
                pass
        
        return methods
    
    def _get_method_parameters(self, func) -> Dict[str, Any]:
        """
        Extract detailed parameter information from a function/method.
        
        Returns:
            Dict containing parameters list, return type, and full signature
        """
        try:
            sig = inspect.signature(func)
            
            parameters = []
            for param_name, param in sig.parameters.items():
                # Skip 'self' and 'cls' parameters
                if param_name in ('self', 'cls'):
                    continue
                
                param_info = {
                    'name': param_name,
                    'type': None,
                    'default': None,
                    'has_default': param.default != inspect.Parameter.empty,
                    'kind': str(param.kind)
                }
                
                # Get type annotation if available
                if param.annotation != inspect.Parameter.empty:
                    param_info['type'] = self._format_type(param.annotation)
                
                # Get default value if available
                if param.default != inspect.Parameter.empty:
                    param_info['default'] = repr(param.default)
                
                parameters.append(param_info)
            
            # Get return type annotation
            return_type = None
            if sig.return_annotation != inspect.Signature.empty:
                return_type = self._format_type(sig.return_annotation)
            
            return {
                'parameters': parameters,
                'return_type': return_type,
                'signature': str(sig)
            }
            
        except Exception as e:
            return {
                'parameters': [],
                'return_type': None,
                'signature': 'Unknown'
            }
    
    def _format_type(self, type_hint) -> str:
        """Format type hint to readable string."""
        try:
            # Handle string annotations
            if isinstance(type_hint, str):
                return type_hint
            
            # Get the name if it's a type
            if hasattr(type_hint, '__name__'):
                return type_hint.__name__
            
            # Handle complex types (Optional, Union, List, etc.)
            return str(type_hint).replace('typing.', '')
        except:
            return str(type_hint)
    
    # ========================================================================
    # DISCOVERY AND LOADING
    # ========================================================================
    
    def discover_all(self, verbose: bool = True) -> Dict[str, Dict]:
        """Discover and load all modules in the search path."""
        if verbose:
            print("="*70)
            print("MODULE DISCOVERY")
            print("="*70)
            print(f"\nSearch path: {self.search_path}")
            print(f"Python version: {sys.version}")
            print(f"Architecture: {sys.maxsize > 2**32 and '64-bit' or '32-bit'}")
        
        # Find module files
        module_files = self.find_module_files()
        
        if verbose:
            print(f"\nFound {len(module_files)} module file(s):")
            for f in module_files:
                print(f"  - {f}")
        
        if not module_files:
            if verbose:
                print("\n⚠ No module files found!")
            return {}
        
        # Load and inspect each module
        if verbose:
            print("\n" + "="*70)
            print("LOADING MODULES")
            print("="*70)
        
        discovered = {}
        
        for filename in module_files:
            module_name = self.extract_module_name(filename)
            
            if verbose:
                print(f"\n📦 Loading: {module_name}")
                print("-"*70)
            
            module = self.load_module(module_name)
            
            if module:
                info = self.get_module_info(module)
                discovered[module_name] = info
                
                if verbose:
                    print(f"✓ Loaded successfully")
                    print(f"  Classes: {len(info['classes'])}")
                    print(f"  Functions: {len(info['functions'])}")
                    print(f"  Attributes: {len(info['attributes'])}")
            else:
                if verbose:
                    print(f"✗ Failed to load")
        
        return discovered
    
    # ========================================================================
    # INFORMATION DISPLAY
    # ========================================================================
    
    def print_detailed_info(self):
        """Print detailed information about all discovered modules."""
        if not self.modules:
            print("\nNo modules loaded. Run discover_all() first.")
            return
        
        print("\n" + "="*70)
        print("DETAILED MODULE INFORMATION")
        print("="*70)
        
        for module_name, info in [(name, self.get_module_info(mod)) 
                                   for name, mod in self.modules.items()]:
            print(f"\n{'='*70}")
            print(f"MODULE: {module_name}")
            print(f"{'='*70}")
            
            if info['doc']:
                print(f"\nDescription: {info['doc']}")
            
            # Print classes
            if info['classes']:
                print(f"\nCLASSES ({len(info['classes'])}):")
                for cls_info in info['classes']:
                    print(f"\n  {cls_info['name']}")
                    if cls_info['doc']:
                        print(f"     {cls_info['doc']}")
                    
                    if cls_info['methods']:
                        print(f"     Methods ({len(cls_info['methods'])}):")
                        for method in cls_info['methods']:
                            method_type = ""
                            if method['is_static']:
                                method_type = " [static]"
                            elif method['is_class']:
                                method_type = " [class]"
                            
                            print(f"       - {method['name']}(){method_type}")
                            if method['doc']:
                                doc_line = method['doc'].split('\n')[0]
                                print(f"         {doc_line}")
            
            # Print functions
            if info['functions']:
                print(f"\nFUNCTIONS ({len(info['functions'])}):")
                for func in info['functions']:
                    print(f"  - {func['name']}()")
                    if func['doc']:
                        doc_line = func['doc'].split('\n')[0]
                        print(f"    {doc_line}")
            
            # Print attributes
            if info['attributes']:
                print(f"\nATTRIBUTES ({len(info['attributes'])}):")
                for attr in info['attributes']:
                    print(f"  - {attr['name']}: {attr['type']}")
    
    def print_summary(self):
        """Print a summary of all discovered modules."""
        summary = self.get_summary()
        
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"\nTotal Modules: {summary['total_modules']}")
        print(f"Total Classes: {summary['total_classes']}")
        print(f"Total Methods: {summary['total_methods']}")
        print(f"Total Functions: {summary['total_functions']}")
        
        print("\n" + "-"*70)
        for module_name, module_info in summary['modules'].items():
            print(f"\n{module_name}")
            print(f"   Classes: {module_info['classes']} {module_info['class_names']}")
            print(f"   Functions: {module_info['functions']} {module_info['function_names']}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all discovered modules."""
        summary = {
            'total_modules': len(self.modules),
            'total_classes': 0,
            'total_methods': 0,
            'total_functions': 0,
            'modules': {}
        }
        
        for module_name, module in self.modules.items():
            info = self.get_module_info(module)
            
            module_summary = {
                'classes': len(info['classes']),
                'functions': len(info['functions']),
                'attributes': len(info['attributes']),
                'class_names': [c['name'] for c in info['classes']],
                'function_names': [f['name'] for f in info['functions']]
            }
            
            summary['total_classes'] += module_summary['classes']
            summary['total_functions'] += module_summary['functions']
            
            for cls_info in info['classes']:
                summary['total_methods'] += len(cls_info['methods'])
            
            summary['modules'][module_name] = module_summary
        
        return summary
    
    # ========================================================================
    # METHOD EXECUTION
    # ========================================================================
    
    def execute_all_methods(self, safe_mode: bool = True, verbose: bool = True):
        """Execute all static/class methods found in modules."""
        if verbose:
            print("\n" + "="*70)
            print("EXECUTING METHODS")
            print("="*70)
        
        if not self.modules:
            print("\nNo modules loaded. Run discover_all() first.")
            return
        
        results = {
            'passed': [],
            'failed': [],
            'skipped': []
        }
        
        for module_name, module in self.modules.items():
            info = self.get_module_info(module)
            
            if verbose:
                print(f"\n{'='*70}")
                print(f"MODULE: {module_name}")
                print(f"{'='*70}")
            
            for cls_info in info['classes']:
                cls = cls_info['object']
                
                if verbose:
                    print(f"\nClass: {cls_info['name']}")
                
                for method in cls_info['methods']:
                    method_name = method['name']
                    method_obj = method['object']
                    test_id = f"{module_name}.{cls_info['name']}.{method_name}"
                    
                    if method['is_static'] or method['is_class']:
                        if verbose:
                            print(f"  Executing: {method_name}()")
                        
                        try:
                            result = method_obj()
                            results['passed'].append({
                                'id': test_id,
                                'result': result
                            })
                            if verbose:
                                print(f"    ✓ Result: {result}")
                                print(f"    ✓ Type: {type(result).__name__}")
                        except TypeError as e:
                            results['skipped'].append({
                                'id': test_id,
                                'reason': 'Requires parameters'
                            })
                            if verbose and not safe_mode:
                                print(f"    ⚠ Skipped: {e}")
                        except Exception as e:
                            results['failed'].append({
                                'id': test_id,
                                'error': str(e)
                            })
                            if verbose:
                                print(f"    ✗ Error: {type(e).__name__}: {e}")
                    elif verbose:
                        print(f"  Instance method: {method_name}() [requires instance]")
            
            # Execute module-level functions
            for func in info['functions']:
                test_id = f"{module_name}.{func['name']}"
                
                if verbose:
                    print(f"\n  Function: {func['name']}()")
                
                try:
                    result = func['object']()
                    results['passed'].append({
                        'id': test_id,
                        'result': result
                    })
                    if verbose:
                        print(f"    ✓ Result: {result}")
                except TypeError:
                    results['skipped'].append({
                        'id': test_id,
                        'reason': 'Requires parameters'
                    })
                except Exception as e:
                    results['failed'].append({
                        'id': test_id,
                        'error': str(e)
                    })
                    if verbose:
                        print(f"    ✗ Error: {type(e).__name__}: {e}")
        
        # Print execution summary
        print(f"\n{'='*70}")
        print("EXECUTION SUMMARY")
        print(f"{'='*70}")
        print(f"✓ Passed: {len(results['passed'])}")
        print(f"✗ Failed: {len(results['failed'])}")
        print(f"⚠ Skipped: {len(results['skipped'])}")
        
        return results
    
    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================
    
    def get_class(self, class_name: str) -> Optional[type]:
        """Get a class by name from any loaded module."""
        for module in self.modules.values():
            info = self.get_module_info(module)
            for cls_info in info['classes']:
                if cls_info['name'] == class_name:
                    return cls_info['object']
        return None
    
    def get_module(self, module_name: str) -> Optional[Any]:
        """Get a loaded module by name."""
        return self.modules.get(module_name)
    
    def call_method(self, class_name: str, method_name: str, *args, **kwargs):
        """Call a static/class method by name."""
        cls = self.get_class(class_name)
        if cls is None:
            raise ValueError(f"Class '{class_name}' not found")
        
        method = getattr(cls, method_name, None)
        if method is None:
            raise ValueError(f"Method '{method_name}' not found in class '{class_name}'")
        
        return method(*args, **kwargs)
    
    # ========================================================================
    # MAIN WORKFLOW
    # ========================================================================
    
    def run_complete_workflow(self, execute_methods: bool = False):
        """Run the complete workflow: discover, inspect, execute."""
        print("\n")
        print("╔" + "="*68 + "╗")
        print("║" + " "*20 + "MODULE MANAGER" + " "*35 + "║")
        print("╚" + "="*68 + "╝")
        print("\nComplete module management solution")
        
        # Step 1: Discover modules
        discovered = self.discover_all()
        
        if not discovered:
            print("\n⚠ No modules discovered!")
            return
        
        # Step 2: Print detailed info
        self.print_detailed_info()
        
        # Step 3: Print summary
        self.print_summary()
        
        # Step 4: Execute methods (optional)
        if execute_methods:
            self.execute_all_methods(safe_mode=True)
        
        print("\n" + "="*70)
        print("WORKFLOW COMPLETE")
        print("="*70)
        
        return discovered

    def main(self):
        """Main function with interactive mode."""
        print("\n")
        print("╔" + "="*68 + "╗")
        print("║" + " "*20 + "MODULE MANAGER" + " "*35 + "║")
        print("╚" + "="*68 + "╝")
        
        # Ask for search path
        print("\n" + "="*70)
        print("SELECT SEARCH PATH")
        print("="*70)
        print(f"\nCurrent directory: {os.getcwd()}")
        print("\nOptions:")
        print("  1. Use current directory")
        print("  2. Enter custom path")
        
        choice = input("\nSelect option (1-2): ").strip()
        
        if choice == '2':
            custom_path = input("Enter folder path: ").strip().strip('"').strip("'")
            if os.path.isdir(custom_path):
                self.search_path = custom_path
                # Update sys.path
                if self.search_path not in sys.path:
                    sys.path.insert(0, self.search_path)
                print(f"✓ Using: {self.search_path}")
            else:
                print(f"✗ Invalid path. Using current directory.")
        
        # Check for conflicts
        conflicts, _ = self.find_conflicts()
        if conflicts:
            print("\n⚠️  Conflicts detected!")
            self.resolve_conflicts(method='ask')
        
        # Run workflow
        self.run_complete_workflow()
        
        # Ask to execute methods
        print("\n" + "="*70)
        response = input("\nExecute all available methods? (y/n): ").strip().lower()
        
        if response == 'y':
            self.execute_all_methods(safe_mode=True)
        
        print("\n" + "="*70)
        print("SESSION COMPLETE")
        print("="*70)
    
    # ========================================================================
    # ANALYSIS FUNCTIONS
    # ========================================================================
    
    def view_all_parameters(self):
        """View all method parameters with types."""
        print("\n" + "="*70)
        print("VIEW ALL PARAMETERS")
        print("="*70)
        
        if not self.modules:
            self.discover_all(verbose=False)
        
        for module_name, module in self.modules.items():
            info = self.get_module_info(module)
            
            print(f"\n{'='*70}")
            print(f"MODULE: {module_name}")
            print(f"{'='*70}")
            
            for cls_info in info['classes']:
                print(f"\nClass: {cls_info['name']}")
                
                for method in cls_info['methods']:
                    print(f"\n  Method: {method['name']}{method['signature']}")
                    
                    if method['parameters']:
                        print(f"  Parameters:")
                        for param in method['parameters']:
                            print(f"    - {param['name']}: {param['type'] or 'Any'}", end="")
                            if param['has_default']:
                                print(f" = {param['default']}", end="")
                            print()
                    
                    if method['return_type']:
                        print(f"  Returns: {method['return_type']}")
    
    def find_by_parameter_type(self, target_type: str = "str"):
        """Find all methods that accept a specific parameter type."""
        print("\n" + "="*70)
        print("FIND METHODS BY PARAMETER TYPE")
        print("="*70)
        
        if not self.modules:
            self.discover_all(verbose=False)
        
        print(f"\nMethods accepting '{target_type}' parameters:")
        
        for module_name, module in self.modules.items():
            info = self.get_module_info(module)
            
            for cls_info in info['classes']:
                for method in cls_info['methods']:
                    for param in method['parameters']:
                        if param['type'] and target_type in param['type']:
                            print(f"\n  {module_name}.{cls_info['name']}.{method['name']}")
                            print(f"    Parameter: {param['name']}: {param['type']}")
    
    def find_no_parameters(self):
        """Find and execute all methods that take no parameters."""
        print("\n" + "="*70)
        print("METHODS WITH NO PARAMETERS")
        print("="*70)
        
        if not self.modules:
            self.discover_all(verbose=False)
        
        print("\nMethods with no parameters (can be executed directly):")
        
        for module_name, module in self.modules.items():
            info = self.get_module_info(module)
            
            for cls_info in info['classes']:
                for method in cls_info['methods']:
                    if not method['parameters'] and (method['is_static'] or method['is_class']):
                        print(f"\n  {cls_info['name']}.{method['name']}()")
                        print(f"    Returns: {method['return_type'] or 'Unknown'}")
                        
                        # Try to execute it
                        try:
                            result = method['object']()
                            print(f"    Result: {result}")
                        except Exception as e:
                            print(f"    Error: {e}")
    
    def generate_docs(self):
        """Generate documentation with parameter information."""
        print("\n" + "="*70)
        print("GENERATE DOCUMENTATION")
        print("="*70)
        
        if not self.modules:
            self.discover_all(verbose=False)
        
        docs = []
        docs.append("# API Documentation\n")
        
        for module_name, module in self.modules.items():
            info = self.get_module_info(module)
            
            docs.append(f"\n## Module: {module_name}\n")
            
            for cls_info in info['classes']:
                docs.append(f"\n### Class: `{cls_info['name']}`\n")
                
                if cls_info['doc']:
                    docs.append(f"{cls_info['doc']}\n")
                
                for method in cls_info['methods']:
                    # Build signature
                    method_type = ""
                    if method['is_static']:
                        method_type = " `@staticmethod`"
                    elif method['is_class']:
                        method_type = " `@classmethod`"
                    
                    docs.append(f"\n#### `{method['name']}{method['signature']}`{method_type}\n")
                    
                    if method['doc']:
                        docs.append(f"{method['doc']}\n")
                    
                    # Parameters
                    if method['parameters']:
                        docs.append("\n**Parameters:**\n")
                        for param in method['parameters']:
                            param_doc = f"- `{param['name']}`"
                            if param['type']:
                                param_doc += f" (`{param['type']}`)"
                            if param['has_default']:
                                param_doc += f" - Default: `{param['default']}`"
                            docs.append(param_doc + "\n")
                    
                    # Return type
                    if method['return_type']:
                        docs.append(f"\n**Returns:** `{method['return_type']}`\n")
        
        documentation = "\n".join(docs)
        
        # Save to file
        doc_path = os.path.join(self.search_path, 'api_documentation.md')
        with open(doc_path, 'w') as f:
            f.write(documentation)
        
        print(f"✓ Documentation saved to {doc_path}")
        print("\nPreview:")
        print(documentation[:1000] + "...")
        
        return doc_path
    
    def export_json(self):
        """Export all parameter information to JSON."""
        print("\n" + "="*70)
        print("EXPORT TO JSON")
        print("="*70)
        
        if not self.modules:
            self.discover_all(verbose=False)
        
        api_data = {}
        
        for module_name, module in self.modules.items():
            info = self.get_module_info(module)
            
            module_data = {
                'classes': {}
            }
            
            for cls_info in info['classes']:
                class_data = {
                    'doc': cls_info['doc'],
                    'methods': {}
                }
                
                for method in cls_info['methods']:
                    method_data = {
                        'signature': method['signature'],
                        'doc': method['doc'],
                        'is_static': method['is_static'],
                        'is_class': method['is_class'],
                        'parameters': method['parameters'],
                        'return_type': method['return_type']
                    }
                    
                    class_data['methods'][method['name']] = method_data
                
                module_data['classes'][cls_info['name']] = class_data
            
            api_data[module_name] = module_data
        
        # Save to JSON
        json_path = os.path.join(self.search_path, 'api_parameters.json')
        with open(json_path, 'w') as f:
            json.dump(api_data, f, indent=2)
        
        print(f"✓ API data saved to {json_path}")
        
        # Show sample
        print("\nSample data:")
        print(json.dumps(api_data, indent=2)[:500] + "...")
        
        return json_path
    
    def validate_calls(self, target_class: str, target_method: str):
        """Check if you have the right parameters before calling."""
        print("\n" + "="*70)
        print("VALIDATE METHOD CALLS")
        print("="*70)
        
        if not self.modules:
            self.discover_all(verbose=False)
        
        for module_name, module in self.modules.items():
            info = self.get_module_info(module)
            
            for cls_info in info['classes']:
                if cls_info['name'] == target_class:
                    for method in cls_info['methods']:
                        if method['name'] == target_method:
                            print(f"\nFound: {target_class}.{target_method}")
                            print(f"Signature: {method['signature']}")
                            
                            # Check parameters
                            if not method['parameters']:
                                print("✓ No parameters required - safe to call")
                                
                                try:
                                    result = method['object']()
                                    print(f"Result: {result}")
                                    return result
                                except Exception as e:
                                    print(f"Error: {e}")
                                    return None
                            else:
                                print("⚠ Parameters required:")
                                for param in method['parameters']:
                                    print(f"  - {param['name']}: {param['type']}")
                                    if not param['has_default']:
                                        print(f"    (REQUIRED)")
                                return None
        
        print(f"\n✗ Method {target_class}.{target_method} not found")
        return None
    
    def find_optional_parameters(self):
        """Find methods with optional (default) parameters."""
        print("\n" + "="*70)
        print("METHODS WITH OPTIONAL PARAMETERS")
        print("="*70)
        
        if not self.modules:
            self.discover_all(verbose=False)
        
        print("\nMethods with optional parameters:")
        
        for module_name, module in self.modules.items():
            info = self.get_module_info(module)
            
            for cls_info in info['classes']:
                for method in cls_info['methods']:
                    optional_params = [p for p in method['parameters'] if p['has_default']]
                    
                    if optional_params:
                        print(f"\n  {cls_info['name']}.{method['name']}()")
                        print(f"  Optional parameters:")
                        for param in optional_params:
                            print(f"    - {param['name']}: {param['type']} = {param['default']}")
    
    def interactive_inspector(self):
        """Interactive parameter inspector."""
        print("\n" + "="*70)
        print("INTERACTIVE PARAMETER INSPECTOR")
        print("="*70)
        
        if not self.modules:
            self.discover_all(verbose=False)
        
        # Collect all methods with parameters
        methods_with_params = []
        
        for module_name, module in self.modules.items():
            info = self.get_module_info(module)
            
            for cls_info in info['classes']:
                for method in cls_info['methods']:
                    if method['parameters']:
                        methods_with_params.append({
                            'module': module_name,
                            'class': cls_info['name'],
                            'method': method
                        })
        
        if not methods_with_params:
            print("No methods with parameters found!")
            return
        
        print(f"\nFound {len(methods_with_params)} methods with parameters:")
        
        for i, item in enumerate(methods_with_params[:10], 1):  # Show first 10
            method = item['method']
            print(f"\n{i}. {item['class']}.{method['name']}{method['signature']}")
            
            for param in method['parameters']:
                param_info = f"     {param['name']}"
                if param['type']:
                    param_info += f": {param['type']}"
                if param['has_default']:
                    param_info += f" = {param['default']}"
                print(param_info)
    
    def smart_execution(self):
        """Execute methods smartly based on parameter requirements."""
        print("\n" + "="*70)
        print("SMART METHOD EXECUTION")
        print("="*70)
        
        if not self.modules:
            self.discover_all(verbose=False)
        
        results = {
            'no_params_success': [],
            'no_params_failed': [],
            'has_params_skipped': []
        }
        
        for module_name, module in self.modules.items():
            info = self.get_module_info(module)
            
            for cls_info in info['classes']:
                for method in cls_info['methods']:
                    if method['is_static'] or method['is_class']:
                        method_id = f"{module_name}.{cls_info['name']}.{method['name']}"
                        
                        if not method['parameters']:
                            # No parameters - try to execute
                            try:
                                result = method['object']()
                                results['no_params_success'].append({
                                    'id': method_id,
                                    'result': result,
                                    'return_type': method['return_type']
                                })
                            except Exception as e:
                                results['no_params_failed'].append({
                                    'id': method_id,
                                    'error': str(e)
                                })
                        else:
                            # Has parameters - skip
                            results['has_params_skipped'].append({
                                'id': method_id,
                                'params': method['parameters']
                            })
        
        # Print summary
        print(f"\n{'='*70}")
        print("SMART EXECUTION SUMMARY")
        print(f"{'='*70}")
        print(f"✓ No params (success): {len(results['no_params_success'])}")
        print(f"✗ No params (failed): {len(results['no_params_failed'])}")
        print(f"⚠ Has params (skipped): {len(results['has_params_skipped'])}")
        
        # Show what was skipped and why
        if results['has_params_skipped']:
            print(f"\nSkipped methods (require parameters):")
            for item in results['has_params_skipped'][:5]:
                print(f"  {item['id']}")
                for param in item['params']:
                    print(f"    - {param['name']}: {param['type']}")
        
        return results
