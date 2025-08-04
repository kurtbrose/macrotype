This project focuses on generating `.pyi` files from live modules.

By its nature most tests are in the form of lines in a py and a corresponding pyi file.

If possible, always test new features by adding new lines to annotations.py and annotations.pyi; document what is tested by variable names and comments in annotations.py.

After making other code changes, regenerate the stub `.pyi` files and run `ruff format` and `ruff check --fix` before committing.
