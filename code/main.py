import os
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
        # add logging configuration
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("main.log"),
                logging.StreamHandler()
            ]
        )


    def main(self):
        """
        Main function to run the script.
        """
        # Example usage of the base_path
        if not hasattr(self, 'base_path'):
            raise AttributeError("Base path is not set. Please initialize the class with a valid system.")
        # Here you can add more functionality as needed
        from util.get_files import get_files
        from util.hr.extract_hr import ExtractHR
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
                                logging.debug(f"Processing subject: {subject} with files: {subject_files}")
                                if file.endswith('.csv'):
                                    hr = ExtractHR(subject_files).extract_hr(file)


        

