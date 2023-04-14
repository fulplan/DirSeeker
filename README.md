# DirSeeker

DirSeeker is a command-line tool written in Python that helps you search for files within directories and subdirectories of your file system.
Installation

    Clone the repository to your local machine:

`
git clone https://github.com/your-username/DirSeeker.git
`

    Navigate to the project directory:


`
cd DirSeeker
`

    Install the required packages using pip:

`
pip install -r requirements.txt
`

-  Usage

DirSeeker provides a simple and easy-to-use interface. To search for files, simply run the command:


`
python dirseeker.py [OPTIONS] DIRECTORY PATTERN
`

Here's a breakdown of the command and its arguments:

    OPTIONS: Any of the following optional arguments:
        -f, --file-only: Only search for files (ignore directories).
        -d, --dir-only: Only search for directories (ignore files).
        -i, --ignore-case: Ignore case when searching for patterns.
        -e, --extension: Only search for files with the specified extension.
    DIRECTORY: The starting directory for the search.
    PATTERN: The pattern to search for. This can be a file name, directory name, or a regular expression.

For example, to search for all files in the current directory and its subdirectories that end with ".txt", you can run:

`
python dirseeker.py -f -e txt 
`

This will return a list of all matching files with their full path.
> License

This project is licensed under the MIT License - see the LICENSE file for details.
Contributing

> Contributions are welcome! If you find a bug or have a suggestion for improvement, please open an issue or submit a pull request.