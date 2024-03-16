
import argparse
import csv
import multiprocessing
import re
import sys
from datetime import datetime
from pathlib import Path


class Searcher:
    """Searcher class for finding patterns in CSV files."""
    
    def __init__(self, 
                 source, 
                 out, 
                 search_file='regex.txt'):
        """
        Initialize the Searcher class
        Args:
            source (str): Full path to directory containing CSV files.
            out (str): Output directory for CSV with IOC hits.
            search_file (str): Name of the search file. Default is regex.txt.
        """
        self.source = source
        self.out = out
        self.search_file = search_file
        self.rgx_dict = {}
        self.str_dict = {}
        self._load_patterns()  # Call load_patterns during initialization

    def _load_patterns(self):
        """
        Load patterns from the search file and compile regex.
        """
        rgx_file = Path.cwd() / self.search_file
        if not rgx_file.is_file():
            sys.exit(f'\nCan\'t find {self.search_file}. This file should be in the same dir as search.py')
        else:
            with rgx_file.open() as csvfile:
                reader = csv.reader(csvfile, delimiter=';')
                try:
                    for row in reader:
                        if any(row):
                            if row[0] == '1':  # regex
                                self.rgx_dict[row[1]] = row[2]
                            elif row[0] == '0':  # simple string
                                self.str_dict[row[1]] = row[2]
                except Exception as e:
                    print(f'\nFormatting issue with row in regex.txt: {e}')
                    print(f'Please inspect: {row}')
        self._compile_regex()  # Call compile_regex after loading patterns

    def _compile_regex(self):
        """
        Compile regex from rgx_dict and track descriptions.
        """
        self.compiled_regex_patterns = {}

        for pattern, description in self.rgx_dict.items():
            try:
                compiled_pattern = re.compile(pattern)
                self.compiled_regex_patterns[pattern] = {'compiled_pattern': compiled_pattern, 'description': description}
            except re.error as e:
                print(f'Error compiling regex pattern "{pattern}": {e}')

    def _find_hits_in_file(self, file):
        """
        Find pattern matches in a single CSV file.
        Args:
            file (Path): Path to the CSV file.
        Returns:
            matches: List of matches found in the file.
        """
        matches = []

        for key, val in self.compiled_regex_patterns.items():
            try:
                compiled_pattern = val['compiled_pattern']
                description = val['description']

                with file.open('r', encoding='utf-8', errors='replace') as fh:
                    for line in fh:
                        if compiled_pattern.search(line):
                            row = [file.name, key, description, line]
                            matches.append(row)
            except Exception as e:
                print(f'Error processing file "{file}": {e}')

        for key, val in self.str_dict.items():
            try:
                with file.open('r', encoding='utf-8', errors='replace') as fh:
                    for line in fh:
                        if key.lower() in line.lower():
                            row = [file.name, key, val, line]
                            matches.append(row)
            except Exception as e:
                print(f'Error processing file "{file}": {e}')

        return matches

    def find_hits(self):
        """
        Searches for hits across multiple files.
        """
        search_path = Path(self.source)
        
        files = [
            file 
            for file in sorted(search_path.rglob('*.csv'), key=lambda file: file.name) 
            if 'SearchResults' not in file.name
        ]

        if len(files) > 0:
            print(f'\nBeginning search. Using {self.search_file} as input file.')
            pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())  # Use all available CPU cores
            results = [pool.apply_async(self._find_hits_in_file, (file,)) for file in files]
            pool.close()

            hits = []

            total_files = len(files)
            total_patterns = len(self.compiled_regex_patterns) + len(self.str_dict)

            print(f'Found {total_files} CSV files. Searching using {total_patterns} patterns...\n')

            start_time = datetime.now()

            for idx, result in enumerate(results, 1):
                matches = result.get()
                hits.extend(matches)
                self._print_progress_bar(idx, total_files, start_time)

            self._write_csv(hits)

        else:
            print(f'No CSV files found in {search_path}')

    @staticmethod
    def _print_progress_bar(iteration, total, start_time):
        """
        Print a progress bar showing the search progress.
        Args:
        iteration (int): Current iteration.
        total (int): Total number of iterations.
        start_time (datetime): Time when the search started.
        """
        length = 50
        percent = ("{0:.1f}").format(100 * (iteration / float(total)))
        filled_length = int(length * (iteration / total))
        bar = '█' * filled_length + '-' * (length - filled_length)
        elapsed_time = datetime.now() - start_time
        print(f'\r|{bar}| {percent}% Complete | Elapsed Time: {elapsed_time}', end='', flush=True)
        # Print New Line on Complete
        if iteration == total:
            print()


    def _write_csv(self, hit_list):
        """
        Write the search results to a CSV file.
        Args:
            hit_list (list): List of search results.
        """
        if not hit_list:
            print('\nNo hits found. Please come again.')
            return
            
        dt = datetime.now()
        outdir = Path(self.out) / 'SearchResults'

        if not outdir.exists():
            outdir.mkdir(parents=True, exist_ok=True)

        out_file = outdir / f'SearchResults_{dt.strftime("%Y%m%d%H%M%S")}.csv'
        header = ['Source File', 'Match', 'Description', 'Found in Line']

        with out_file.open('w', newline='', errors='replace') as fh:
            csv_writer = csv.writer(fh)
            csv_writer.writerow(header)

            for hit in hit_list:
                csv_writer.writerow(hit)

        print(f'\nFound {len(hit_list)} hits. Check {out_file.name} for details.')


def main():
    """
    Main function to initiate the search.
    """
    searcher = Searcher(args.source, args.out, args.search)
    searcher.find_hits()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IOC finder', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-s', '--source', type=str, required=True,
                        help='Full path to directory containing csv/text files')
    parser.add_argument('-o', '--out', type=str, required=True, help='Output directory for CSV with IOC hits')
    parser.add_argument('--search', type=str, action='store', nargs='?', required=True, const='regex.txt',
                        help=' file to use. must be placed in cwd. Default is regex.txt')
    args = parser.parse_args()
    main()
