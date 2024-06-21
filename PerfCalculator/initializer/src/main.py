import create_folders
import i_fetch_contest_results
import i_calculate
import update_files

if __name__ == "__main__":
    create_folders.create_folders()
    i_fetch_contest_results.fetch_results()
    i_calculate.calculate()
    update_files.update_files()
