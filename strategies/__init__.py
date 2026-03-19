import pkgutil
import importlib
from pathlib import Path

# 1. Get the path of the current directory (the 'strategies' folder)
package_dir = Path(__file__).resolve().parent

# 2. Iterate through every file in the directory
for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
    # 3. Ignore base classes or the registry itself
    if module_name not in ('base', 'registry'):
        # 4. Programmatically import the module.
        # This triggers the @register decorators automatically!
        importlib.import_module(f"strategies.{module_name}")
