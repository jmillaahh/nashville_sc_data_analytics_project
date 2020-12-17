from data_processing import *
import time

if __name__ == '__main__':
    # instantiate a CurrentMatch object
    GenerateReport = CurrentMatch()

    # process given files and record time taken to complete processing
    start = time.time()
    GenerateReport.process_jsonl_file()
    end = time.time()

    # populate the output file and report processing duration
    GenerateReport.write_output(end - start)
