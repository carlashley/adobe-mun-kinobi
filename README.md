# adobe-mun-kinobi
Experimental bulk importer for Adobe Creative Cloud Packages. *NO SUPPORT PROVIDED*.

- Download packages from the Adobe admin portal
- Remove all extended attributes from downloaded zip files/package files (`xattr -rc [folder]`)
- ...
- Profit

# Usage:
```
usage: adobe-mun-kinobi [-h] [--adobe-dir [dir]] [--category [category]] [--catalog [catalog]] [--developer [developer]] [--munki-repo [dir]] [--munki-subdir [dir]]
                        [--min-munki-version [min munki version]] [--min-os-ver [min os ver]] [--suffix [suffix]] [--import-sap-code [code] [[code] ...]] [--list-sap-codes] [-n]

optional arguments:
  -h, --help            show this help message and exit
  --adobe-dir [dir]     directory containing unzipped Adobe installers
  --category [category]
                        override the default category 'Creativity' for all packages processed
  --catalog [catalog]   override the default catalog 'testing' for all packages processed
  --developer [developer]
                        override the default developer 'Adobe' for all packages processed
  --munki-repo [dir]    override or use a custom munki repo path, defaults to 'file:///Volumes/munki_repo'
  --munki-subdir [dir]  override the default package directory 'apps' for all packages processed
  --min-munki-version [min munki version]
                        override the default minimum version of munki '2.1' for all packages processed
  --min-os-ver [min os ver]
                        override the minimum macOS version for all packages processed
  --suffix [suffix]     override the default display name suffix 'Creative Cloud' for all packages processed
  --import-sap-code [code] [[code] ...]
                        import specific Adobe products by SAP code, use '--list-sap-codes' to view codes
  --list-sap-codes      list Adobe products SAP codes
  -n, --dry-run         performs a dry run (outputs import commands to stdout)
```
