import os
import sys
import csv
import logging
import argparse
import pandas as pd

logger = logging.getLogger('extensionlog')


class ExtensionLog(object):
    def __init__(self, args):
        """
        Adds missing time steps to a extension log CSV file.
        @param Namespace object args: User inputs
        """
        self.csv_log_file = args.csv_log_file
        self.out_csv_log_file = args.out_csv_log_file
        self.time_step_column = args.time_step_column
        self.time_interval = args.time_interval
        self.min_time = args.min_time
        self.max_time = args.max_time
        self.group_by_column = args.group_by_column

    def output_file_path(self, file_name):
        """
        Add .csv extension if doesn't have one.
        @return str out_file_path: Output CSV file path
        """
        try:
            in_csv_dir = os.path.dirname(self.csv_log_file)
            in_csv_file_name = os.path.basename(self.csv_log_file).split('.')[0]
            out_csv_file_name = file_name.split('.')[0]

            if in_csv_file_name.lower() == out_csv_file_name.lower():
                raise ValueError
            else:
                out_file_path = os.path.join(in_csv_dir, out_csv_file_name + '.csv')
                return out_file_path

        except ValueError:
            sys.stdout('Input CSV file name and output file name is the same. Change output file name.')
        except Exception as e:
            error_log(logger, e)

    def out_csv(self, data):
        """
        Write data to CSV file.
        @param List[dict] data: The data with all missing steps.
        """
        try:
            logger.info('Write data to CSV file.')
            keys = data[0].keys()
            out_log = self.output_file_path(self.out_csv_log_file)

            if out_log:
                with open(out_log, 'w', newline='') as output_file:
                    dict_writer = csv.DictWriter(output_file, keys)
                    dict_writer.writeheader()
                    dict_writer.writerows(data)
                logger.info(f'{out_log} created.')

        except Exception as e:
            error_log(logger, e)

    def add_time_steps(self, df, time_steps):
        """
        Add missing time steps (no groupby query).
        @param DataFrame df: a DataFrame object created from a CSV file.
        @param List[int] time_steps: all time steps.
        @return List[dict] data: data time steps.
        """
        try:
            logger.info('Add time steps (no groupby query.')
            data = []
            data_time_steps = list(df[self.time_step_column])

            if set(time_steps) != set(data_time_steps):
                logger.info('Found missing time steps.')
                for step in time_steps:
                    if step not in data_time_steps:
                        row = {field: 0 for field in list(df.columns)}
                        row[self.time_step_column] = step
                    else:
                        row = df.query(f'{self.time_step_column} == {step}').to_dict('records')[0]
                    data.append(row)
                return data
            else:
                logger.info('No missing time steps.')

        except Exception as e:
            error_log(logger, e)

    def add_time_steps_groupby(self, df, time_steps):
        """
        Add missing time steps (groupby query).
        @param DataFrame df: a DataFrame object created from a CSV file.
        @param List[int] time_steps: all time steps.
        @return List[dict] data: data time steps.
        """
        try:
            logger.info('Add time steps using group by query.')
            names = df[self.group_by_column].unique()
            data = []
            contain_space = False

            for name in names:
                select_by_name_df = df.query(f'{self.group_by_column} == "{name}"').sort_values(
                    by=self.time_step_column)
                # Remove a space at zero (e.g. '  SpruceBudworm')
                if name.startswith(' '):
                    contain_space = True
                    select_by_name_df[self.group_by_column] = name[1::]
                data_time_step = list(select_by_name_df[self.time_step_column])

                # IF there are missing time steps
                if set(time_steps) != set(data_time_step):
                    logger.info('Found missing time steps.')
                    for step in time_steps:
                        if step not in data_time_step:
                            row = {field: 0 for field in list(df.columns)}
                            row[self.time_step_column] = step
                            if contain_space:
                                row[self.group_by_column] = name[1::]
                            else:
                                row[self.group_by_column] = name
                        else:
                            row = select_by_name_df.query(f'{self.time_step_column} == {step}').to_dict('records')[0]
                        data.append(row)
                else:
                    logger.info('No missing time steps.')
            return data

        except Exception as e:
            error_log(logger, e)

    def checkTimeSteps(self):
        """
        Runs methods and output CSV file.
        """
        try:
            logger.info('Add missing time steps.')
            is_csv = os.path.basename(self.csv_log_file).endswith('.csv')

            # Check the input file is CSV file and it exists.
            if is_csv and os.path.exists(self.csv_log_file):
                df = pd.read_csv(self.csv_log_file)
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove empty columns
                time_steps = [i for i in range(self.min_time, self.max_time + self.time_interval, self.time_interval)]

                if self.group_by_column is not None:  # IF groupby parameter is given
                    data = self.add_time_steps_groupby(df, time_steps)
                else:
                    # Call
                    data = self.add_time_steps(df, time_steps)

                self.out_csv(data)  # Write to CSV file
            else:
                raise FileNotFoundError

        except FileNotFoundError:
            logger.error(f'{self.csv_log_file} does not exist.')
        except Exception as e:
            error_log(logger, e)


def set_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def error_log(logger, err):
    """
    Set error log format and write to a log file.
    @param logger logger: Logger object
    @param Exception err: Exception object
    """
    trace = []
    tb = err.__traceback__
    while tb is not None:
        path = os.path.normpath(tb.tb_frame.f_code.co_filename)
        path_last_two_level = '/'.join(path.split(os.sep)[-2:])
        trace.append({
            "filename": path_last_two_level,
            "name": tb.tb_frame.f_code.co_name,
            "line": tb.tb_lineno
        })
        tb = tb.tb_next
    last_trace = trace[-1]
    msg = f'{type(err).__name__}\t{last_trace["filename"]}:{last_trace["line"]}\n\t{str(err)}'
    logger.error(msg)


def extantFile(x):
    """
    'Type' for argparse - checks that file exists but does not open.
    """
    if not os.path.exists(x):
        raise argparse.ArgumentError(x, f"{x} does not exist")
    return x

def parseArguemnts(argv):
    parser = argparse.ArgumentParser(description='LANDVIZ PreProcTool')

    subparsers = parser.add_subparsers(title="actions", dest="command")
    # timesteps tool
    parserTimeSteps = subparsers.add_parser("timesteps", help="Creates a new CSV file with all time steps.")
    timeStepsRequired = parserTimeSteps.add_argument_group('required arguments')
    timeStepsRequired.add_argument("-i", "--inputfile", dest="csv_log_file", required=True, type=extantFile,
                                   help="Extension CSV log File", metavar="FILE")
    timeStepsRequired.add_argument("-f", "--outputfile", dest="out_csv_log_file", required=True, type=str,
                                   help="Output CSV file name")
    timeStepsRequired.add_argument("-ts_c", "--timestep-column", dest="time_step_column", required=True, type=str,
                                   help="Time steps")
    timeStepsRequired.add_argument("-ts_i", "--timestep-interval", dest="time_interval", required=True, type=int,
                                   help="Time step interval")
    timeStepsRequired.add_argument("-ts_min", "--min-time", dest="min_time", required=True, type=int,
                                   help="Minimum time step")
    timeStepsRequired.add_argument("-ts_max", "--max-time", dest="max_time", required=True, type=int,
                                   help="Maximum time step")
    parserTimeSteps.add_argument("-g", "--groupby", dest="group_by_column", required=False, type=str, default='',
                                 help="Group by column name")

    return (parser.parse_args(argv), parser)


def main(argv):
    # print(logging.getLogger().manager.loggerDict.keys())
    try:
        # parse commandline arguments
        args, parser = parseArguemnts(argv)
        if args.command != None:
            logger.info('Check time steps')
            if args.command == 'timesteps':
                timesteps = ExtensionLog(args)
                timesteps.checkTimeSteps()
            logger.info('Done')
            logging.shutdown()
        else:
            logging.shutdown()
            parser.print_help()

    except SystemExit:
        logging.shutdown()# argparse -h
        sys.exit(0)
    except Exception as err:
        logging.shutdown()
        error_log(logger, err)
        logger.info('Failed to run timesteps')


if __name__ == '__main__':
    set_logger()
    main(sys.argv[1:])
