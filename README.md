# searcher
IOC finder. Search CSV files using regex/strings

searcher is intended to be used with parsed output from forensic artifacts, e.g., CSV output for MFT, program execution artifacts, event logs, etc. The default search uses regex.txt which contains known IOCs and other potential items of interest. searcher will recursively search for CSV files under the directory specified as the source at the command-line.

## example usage

use default regex.txt

`python search.py -s \path\to\src_dir -o \path\to\out_dir --search`

use your own

`python search.py -s \path\to\src_dir -o \path\to\out_dir --search yourfile.txt`
