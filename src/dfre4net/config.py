import inspect
import json
import logging
import os
import sys
from pathlib import Path

# Name of local config file
DEFAULT_CONFIG_FILE = Path('../config.json')

class Config:
    """
        Manage configuration for agent

    """

    def __init__(self, config_file: Path = DEFAULT_CONFIG_FILE):

        self.config_file = config_file
        self.json_config = {}

        # load immediately the local config
        self.load_local_config(self.config_file)

        self.validateConfig()

    @property
    def config(self) -> dict:
        return self.json_config
    @property
    def parameters(self) -> dict:
        if not self.json_config["parameters"]: raise RuntimeError("Invalid configuration: no 'parameters' section")
        return self.json_config["parameters"]
    @property
    def L0_input(self) -> dict:
        if not self.json_config["L0_input"]: raise RuntimeError("Invalid configuration: no 'L0_input' section")
        return self.json_config["L0_input"]
    @property
    def L2_input(self) -> dict:
        if not self.json_config["L2_input"]: raise RuntimeError("Invalid configuration: no 'L2_input' section")
        return self.json_config["L2_input"]
    @property
    def output(self) -> dict:
        if not self.json_config["output"]: raise RuntimeError("Invalid configuration: no 'output' section")
        return self.json_config["output"]
    @property
    def pre_processing(self) -> dict:
        if not self.json_config["pre-processing"]: raise RuntimeError("Invalid configuration: no 'pre-processing' section")
        return self.json_config["pre-processing"]
    @property
    def processing(self) -> dict:
        if not self.json_config["processing"]: raise RuntimeError("Invalid configuration: no 'processing' section")
        return self.json_config["processing"]

    def get(self, key: str):
        if not self.json_config["parameters"]: raise RuntimeError("Invalid configuration: no 'parameters' section")
        if key in self.json_config["parameters"]:
            return self.json_config["parameters"][key]
        raise RuntimeError(f"Can't find key {key} in config 'parameters' section")

    def load_local_config(self, config_file) -> None:

        """
        load the .json config file,
        """
        logging.debug(f"--> <--")

        DIR = Path(os.path.abspath(__file__)).parent
        config_file = DIR / self.config_file
        if not config_file.exists: 
            raise ValueError(f"{__name__}::{inspect.currentframe().f_code.co_name}(): The config file '{config_file}'' does not exist.")
        if not config_file.is_file: 
            raise ValueError(f"{__name__}::{inspect.currentframe().f_code.co_name}(): The config file {config_file} is not a file.")
        try:
            with open(config_file) as data_file:
                logging.info(f"loading configuration from: {(repr(config_file))}")
                content = data_file.read()
                self.json_config = json.loads(content)
        except IOError:
            logging.error(f"*E* failed to open {config_file}")
            sys.exit(0)
        except EnvironmentError:
            # This is a fatal error
            logging.error(f"*E* failed to open {config_file}")
            sys.exit(0)
        except Exception as e:
            logging.error(f"*E* trap exception {repr(e)}")
            sys.exit(0)

        ## Loading of configuration ok, do some basic verification
        if self.json_config["L0_input"] and self.json_config["L0_input"]["type"]=="file":
            self.config["L0_input"]["src"] = self.getAndTestPath(self.json_config["L0_input"]["src"])

        if self.json_config["L2_input"] and self.json_config["L2_input"]["type"]=="file":
            self.config["L2_input"]["src"] = self.getAndTestPath(self.json_config["L2_input"]["src"])
            self.config["L2_input"]["src2"] = self.getAndTestPath(self.json_config["L2_input"]["src2"])

    def getAndTestPath(self, path: str) -> Path:

        """
        test file path
        """
        DIR = Path(os.path.abspath(__file__)).parent
        input_file = DIR / Path("../"+path)
        if not input_file.exists:
            logging.error(f"*E* input file {input_file} does not exists")
            raise ValueError(f"*E* input file {input_file} does not exists")
        if not input_file.is_file:
            logging.error(f"*E* input file {input_file} is not a file.")
            raise ValueError(f"*E* input file {input_file} is not a file.")

        logging.info(f"Check input file {input_file}: Ok!")
        return input_file

    def validateConfig(self) -> None:

        """
        Do some config validation
        """
        
        # Verify config file section other than processing/pre-processing
        mandatory = {   "L0_input": ["type", "src"],
                        "L2_input": ["type", "src"],
                        "output": ["type", "endpoint", "enable"],
                        "parameters": ["use_l2_feedback", "l1decomp_batch", "l2decomp_batch", "max_loops", "max_batchs", "dump_l0", "dump_l1",
                                        "dump_l2", "top_l1_stats", "top_l2_stats"]
                    }   
        for section in mandatory:
            mandatory_keys = mandatory[section]
            for key in mandatory_keys: 
                if key not in self.config[section]: 
                    logging.info(f"{key} not found in self.config[{section}]")
                    raise Exception(f"{key} not found in self.config[{section}]")

        # Verify config file section processing/pre-processing
        sections = ["pre-processing", "processing"]
        common_mandatory_keys = ["id", "strategy"]
        mandatory_keys_per_strategy = {
            "max": ["target_prop", "target_kg"],
            "formula": ["target_prop", "target_kg", "formula"],
            "default": ["target_prop", "target_kg", "support_prop", "support_kg"],
            "string": ["target_prop", "target_kg", "support_prop", "support_kg"],
            "merge": ["support_kg", "target_kg"],
            "radius": ["target_prop", "target_kg", "support_prop", "support_kg"],
            'inc': ["target_prop", "target_kg", "support_prop", "support_kg"]
        }
        for section in sections:
            for phase in self.config[section]:
                phase = self.config[section][phase]
                if "strategy" not in phase:
                    logging.info(f"'strategy' key not found for self.config[{section}][{phase}]")
                    raise Exception(f"'strategy' key not found for self.config[{section}][{phase}]")
                if phase["strategy"] not in mandatory_keys_per_strategy:
                    logging.info(f"Not supported strategy for self.config[{section}][{phase}]: '{phase['strategy'] }'")
                    raise Exception(f"Not supported strategy for self.config[{section}][{phase}]: '{phase['strategy'] }'")
                mandatory_keys = common_mandatory_keys + mandatory_keys_per_strategy[phase["strategy"]]
                for key in  mandatory_keys: 
                    if key not in phase: 
                        logging.info(f"'{key}' not found in self.config[{section}][{phase}]")
                        raise Exception(f"'{key}' not found in self.config[{section}][{phase}]")
                



