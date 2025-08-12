import os
import sys
import logging
class Main:

    def __init__(self, system):
        if system is None:
            raise ValueError("System cannot be None")
        if system == "Argon":
            self.base_path = "/Shared/vosslabhpc/Projects/BOOST/"
        elif system == "Home":
            self.base_path = "/mnt/lss/Projects/BOOST/"
        elif system == "vosslnx":
            self.base_path = "/mnt/lss/vosslabhpc/Projects/BOOST/"
        self.zone_path = f"{self.base_path}InterventionStudy/1-projectManagement/participants/ExerciseSessionMaterials/Intervention Materials/BOOST HR ranges.xlsx"

        self.out_path = '../qc_out.csv'


        # add logging configuration
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("main.log", mode="w", encoding="utf-8"), # mode = w will allow for logging to NOT APPEND - then we don't have crazy logs
                logging.StreamHandler()
            ]
        )


    def main(self):
        """
        Main function to run the script.
        """
        err_master = {}
        # Example usage of the base_path
        if not hasattr(self, 'base_path'):
            raise AttributeError("Base path is not set. Please initialize the class with a valid system.")
        # Here you can add more functionality as needed
        from util.get_files import get_files
        from util.hr.extract_hr import extract_hr
        from util.zone.extract_zones import extract_zones
        from qc.sup import QC_Sup
        for project in ["InterventionStudy", "ObservationalStudy"]:
            project_path = os.path.join(self.base_path, project, "3-Experiment", "data", "polarhrcsv")
            if os.path.exists(project_path):
                for session in ["Supervised", "Unsupervised"]:
                    session_path = os.path.join(project_path, session)
                    logging.debug(f"Processing session: {session_path}")
                    if os.path.exists(session_path):
                        # return the files dict that contains base_path and list of files for each base_path
                        files = get_files(session_path)
                        # extract hr from each file
                        for subject, subject_files in files.items():
                            for file in subject_files:
                                if file.lower().endswith('.csv'):
                                    hr = extract_hr(subject_files)
                                    zones = extract_zones(self.zone_path, subject)
                                    err = QC_Sup(hr, zones).main()

                                    if subject not in err_master:
                                        # first time: create a list with this one error
                                        err_master[subject] = [[file,err]]
                                    else:
                                        # append to the existing list
                                        err_master[subject].append([file,err])
        err_master = {
            subject: [e for e in errs if e]
            for subject, errs in err_master.items()
        }
        from qc.save_qc import save_qc
        save_qc(err_master, self.out_path)
        return err_master


if __name__ == '__main__':
    if sys.argv[1]:
        if sys.argv[1] in ["Argon", "Home", "vosslnx"]:
            Main(system=sys.argv[1]).main()
        else:
            raise ValueError("""First Argument is not one of the desired systems: 
            The argument must be one of the following:
            vosslnx = the vosslab linux machine used for automation
            Argon = the Argon HPC
            Home = My (Zak) personal linux machine mount
            """)
    else:
        raise ValueError("""First Argument does not exist.
        The argument must be one of the following:
        vosslnx = the vosslab linux machine used for automation
        Argon = the Argon HPC
        Home = My (Zak) personal linux machine mount
        """)




        

