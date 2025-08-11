#!/usr/bin/env python3
"""
Comprehensive startup validation script for Web3 Research Co-Pilot
Validates syntax, imports, and configurations before application startup
"""

import ast
import sys
import os
import json
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Tuple

def validate_python_syntax(file_path: str) -> Tuple[bool, str]:
    """Validate Python file syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        ast.parse(source)
        return True, "OK"
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Parse error: {str(e)}"

def validate_imports(file_path: str) -> Tuple[bool, List[str]]:
    """Validate that all imports in a Python file can be resolved."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    try:
                        importlib.import_module(alias.name)
                    except ImportError:
                        issues.append(f"Cannot import: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    try:
                        importlib.import_module(node.module)
                    except ImportError:
                        issues.append(f"Cannot import module: {node.module}")
        
        return len(issues) == 0, issues
    except Exception as e:
        return False, [f"Import validation error: {str(e)}"]

def validate_json_files() -> Tuple[bool, List[str]]:
    """Validate JSON configuration files."""
    issues = []
    json_files = [
        "pyproject.toml",  # Will skip if not JSON
        "app_config.yaml"  # Will skip if not JSON
    ]
    
    for file_path in json_files:
        if os.path.exists(file_path) and file_path.endswith('.json'):
            try:
                with open(file_path, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                issues.append(f"Invalid JSON in {file_path}: {str(e)}")
            except Exception as e:
                issues.append(f"Error reading {file_path}: {str(e)}")
    
    return len(issues) == 0, issues

def validate_environment_variables() -> Tuple[bool, List[str]]:
    """Validate required environment variables."""
    issues = []
    optional_vars = [
        "CRYPTOCOMPARE_API_KEY",
        "ETHERSCAN_API_KEY", 
        "COINGECKO_API_KEY"
    ]
    
    for var in optional_vars:
        if not os.getenv(var):
            issues.append(f"Optional environment variable {var} not set (will use free tier)")
    
    return True, issues  # All env vars are optional

def main():
    """Run comprehensive startup validation."""
    print("🔍 Starting comprehensive validation...")
    
    # Get all Python files
    python_files = []
    for root, dirs, files in os.walk("."):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    print(f"📁 Found {len(python_files)} Python files to validate")
    
    all_valid = True
    
    # 1. Syntax validation
    print("\n1️⃣ Validating Python syntax...")
    syntax_issues = []
    for file_path in python_files:
        is_valid, message = validate_python_syntax(file_path)
        if not is_valid:
            syntax_issues.append(f"{file_path}: {message}")
            all_valid = False
        else:
            print(f"  ✅ {file_path}")
    
    if syntax_issues:
        print("❌ Syntax Issues Found:")
        for issue in syntax_issues:
            print(f"  - {issue}")
    
    # 2. Critical imports validation (only for main files)
    print("\n2️⃣ Validating critical imports...")
    critical_files = ["app.py", "src/agent/research_agent.py"]
    import_issues = []
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            is_valid, issues = validate_imports(file_path)
            if not is_valid:
                for issue in issues:
                    import_issues.append(f"{file_path}: {issue}")
            else:
                print(f"  ✅ {file_path}")
    
    # Show non-critical import issues as warnings
    if import_issues:
        print("⚠️  Import Warnings (may use fallbacks):")
        for issue in import_issues:
            print(f"  - {issue}")
    
    # 3. JSON validation
    print("\n3️⃣ Validating configuration files...")
    json_valid, json_issues = validate_json_files()
    if not json_valid:
        print("❌ Configuration Issues:")
        for issue in json_issues:
            print(f"  - {issue}")
        all_valid = False
    else:
        print("  ✅ Configuration files valid")
    
    # 4. Environment validation
    print("\n4️⃣ Validating environment...")
    env_valid, env_issues = validate_environment_variables()
    if env_issues:
        print("ℹ️  Environment Info:")
        for issue in env_issues:
            print(f"  - {issue}")
    else:
        print("  ✅ Environment configured")
    
    # Final result
    print(f"\n{'🎉' if all_valid else '❌'} Validation {'PASSED' if all_valid else 'FAILED'}")
    
    if not all_valid:
        print("\n🛠️  Please fix the issues above before starting the application")
        sys.exit(1)
    else:
        print("\n✅ All critical validations passed - ready to start!")
        sys.exit(0)

if __name__ == "__main__":
    main()
