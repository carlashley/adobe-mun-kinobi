from argparse import Namespace
from pathlib import Path

from implib import arguments
from implib import discover
from implib import munkiimport
from implib import package
from implib import pkginfo


def munki_kwargs(args: Namespace, pkg: package.AdobePackage) -> dict:
    """Return the arguments to pass through to munkiimport"""
    display_name = f"{pkg.display_name} {args.suffix}"
    min_os_ver = args.min_os_ver or pkg.min_os
    result = {"--category": args.category,
              "--catalog": args.catalog,
              "--developer": args.developer,
              "--repo_url": args.munki_repo,
              "--subdirectory": args.munki_subdir,
              "--minimum_os_version": min_os_ver,
              "--displayname": display_name,
              "--description": display_name,
              "--name": pkg.pkg_name,
              "--icon": pkg.icon,
              "--minimum_munki_version": args.min_munki_ver,
              "--arch": pkg.arch,
              "--uninstallerpkg": pkg.uninstaller,
              "--pkgvers": pkg.version}

    return result


def process():
    args = arguments.construct()

    if args.list_sap_codes:
        package.list_sap_codes()

    munki_repo = args.munki_repo or discover.munki_repo()
    existing_pkgs = pkginfo.existing_pkginfo(Path(munki_repo))
    packages = discover.adobe_packages(Path(args.adobe_dir))
    imported = list()

    print(f"Gathering Adobe installer attributes from packages in {args.adobe_dir!r} ...")
    if args.dry_run:
        print("  Note: basename values are used in the dry run output for brevity.")

    for app, files in packages.items():
        pkg = package.process_package(files["installer"], files["uninstaller"], files.get("dmg_file"))
        pkg.imported = any([pkg.pkginfo_file in str(f) for f in existing_pkgs])

        if args.min_os_ver:
            pkg.min_os = args.min_os_ver

        if not pkg.imported and pkg.sap_code in args.import_sap_code:
            munkiimport_args = munki_kwargs(args, pkg)
            pkginfo_file = munkiimport.package(pkg, dry_run=args.dry_run, **munkiimport_args)

            if pkg.receipts:
                pkginfo.update(pkginfo_file, args.dry_run, pkg.receipts)

            if pkginfo_file:
                imported.append(pkginfo_file)
        else:
            if pkg.sap_code in args.import_sap_code:
                print(f"Skipping {pkg.pkg_name!r}, it appears to have previously been imported (existing pkginfo: {pkg.pkginfo_file!r})")

    if imported and not args.dry_run:
        munkiimport.makecatalogs(munki_repo)


if __name__ == "__main__":
    process()
