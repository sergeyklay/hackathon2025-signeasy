import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional, Union

from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)

from se.modules.data_collector import JSONLCollector
from se.utils import clean_json_string, load_prompt

logger = logging.getLogger("se.llama_analyzer")


def default_prompts() -> dict:
    return {
        "document_type": load_prompt("document_type"),
        "obligations": load_prompt("obligations"),
        "risks": load_prompt("risks"),
        "dates": load_prompt("dates"),
        "signature_fields": load_prompt("signature_fields"),
    }


class LlamaAnalyzer:
    """A dynamic analyzer that supports adaptive interaction with the user."""

    def __init__(self, persist_dir: Union[str, Path]):
        self.persist_dir = persist_dir
        self.additional_context = []
        self.index = None
        self.query_engine = None

        # Initialize data collector for responses
        responses_file = Path(self.persist_dir) / "data" / "llm_responses.jsonl"
        self.response_collector = JSONLCollector(responses_file)
        self.index_base_dir = Path(self.persist_dir) / "index"

    def add_context(self, context):
        """Add additional context for the analysis."""
        if context not in self.additional_context:
            self.additional_context += [context]

    def _load_index(self, file: str):
        """Load the index from the persisted storage or build it from the given text or file."""
        # Check if persisted storage exists
        index_persist_dir = str(self.index_base_dir / os.path.basename(file))

        # Load documents and build in-memory index.
        if not os.path.exists(index_persist_dir):
            docs = SimpleDirectoryReader(input_files=[file]).load_data()
            self.index = VectorStoreIndex.from_documents(docs)

            # Persist the index to storage
            self.index.storage_context.persist(persist_dir=index_persist_dir)
        else:
            storage_context = StorageContext.from_defaults(
                persist_dir=index_persist_dir
            )
            self.index = load_index_from_storage(storage_context)

        # Create a query engine if not already initialized
        if not self.query_engine:
            logger.info("Initializing query engine from the index...")
            self.query_engine = self.index.as_query_engine()

    def query(self, prompt, name=None):
        """Query the index with the given prompt."""
        # Run the query
        response = self.query_engine.query(prompt)  # type: ignore
        result = str(response).strip()

        # Remove ```json from the start and ``` from the end using regex
        if result.startswith("```"):
            result = clean_json_string(result)

        # Store the response with metadata
        data = {"prompt": prompt, "response": json.loads(result)}
        self.response_collector.store(data, name)

        return result

    def determine_analysis_steps(self, file: str) -> dict:
        """Determine document type and necessary analysis steps.

        :param file: Path to the document file.
        :return: JSON response with analysis steps.
        """
        # Load or build the index
        self._load_index(file)

        # Run the initial query to determine steps
        prompt = load_prompt("initial_analysis")
        response = self.query(prompt, "analysis_steps")

        # Filter out the steps that are not applicable
        steps = json.loads(response)
        filtered_steps = {
            "document_type": (
                steps["document_type"] if "document_type" in steps else "Unknown"
            ),
            "analysis_steps": [
                step for step in steps["analysis_steps"] if step["applicable"]
            ],
        }

        return filtered_steps

    def analyze_text(self, file: str, steps: dict, prompt: Optional[str] = None):
        """Analyze the given text using LlamaIndex (VectorStoreIndex)."""
        logger.info("Start analyzing...")

        # Load or build the index
        self._load_index(file)

        responses = {}
        prompts = {}
        if "document_type" in steps:
            responses["document_type"] = json.dumps(
                {"document_type": steps["document_type"]}
            )

        if prompt:
            logger.info("Using custom prompt for analysis...")
            key = f"custom_prompt_{hashlib.sha256(prompt.encode()).hexdigest()}"
            prompts[key] = prompt
        else:
            logger.info("Building prompts for analysis steps...")
            for step in steps["analysis_steps"]:
                logger.info(f"Preparing prompt for: {step['category']}")
                defaults = default_prompts()
                if step["category"] not in defaults:
                    logger.info(
                        f"Missing prompt for '{step['category']}', building a generic prompt..."
                    )
                    prompt = self._build_generic_prompt(step)
                    prompts[step["category"]] = prompt
                else:
                    prompts[step["category"]] = defaults[step["category"]]

        logger.info(f"Prompts to use for analysis: {prompts.keys()}")

        # Query the index for each prompt and store the results.
        for key, prompt in prompts.items():
            if len(responses) and prompt:
                logger.debug("Using additional context for the query")
                prompt += "\nThe following information have been already extracted:\n"
                for r in responses.values():
                    prompt += f"{r}\n"

            logger.debug(f"Performing query for key '{key}' with prompt: {prompt}")
            responses[key] = self.query(prompt, key)

        # Build a structured result dictionary
        result = {}
        for key, response in responses.items():
            try:
                result.update(json.loads(response))
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON for key {key}: {response}")
                result[key] = response

        return result

    def _build_generic_prompt(self, step: dict) -> str:
        """Build a generic prompt for the given step.

        This function is responsible for generating a prompt for a given step.
        Typical return values are dependent on the type of the step.
        Possible types are 'table', 'list' and 'text'.

        For table:

           Some reason for the step.
           Use step-by-step reasoning to extract all TERMS from the document.
           Format the result in JSON:
           {
             "TERMS": [
               {
                 "KEY 1": "Description of the field",
                 "KEY 1": "Description of the field"
               },
               ...
             ]
           }
           Use the following fields to describe the table: "KEY 1", "KEY 2", ...
           If no TERMS is found, return {"TERMS": []}.
           Your entire response/output is going to consist of a single JSON object {}, and you will NOT wrap it within JSON markdown markers.

        For list:

           Some reason for the step.
           Use step-by-step reasoning to extract all TERMS from the document.
           Format the result in JSON:
           {
             "TERMS": [
               "description 1",
               "description 2",
               ...
             ]
           }
           If no TERMS is found, return {"TERMS": []}.
           Your entire response/output is going to consist of a single JSON object {}, and you will NOT wrap it within JSON markdown markers.

        For text:

           Some reason for the step.
           Use step-by-step reasoning to extract TERM from the document.
           Format the result in JSON:
           {
             "TERM": "Description of the field"
           }
           If no TERM is found, return {"TERM": "Unknown"}.
           Your entire response/output is going to consist of a single JSON object {}, and you will NOT wrap it within JSON markdown markers.
        """
        if not step:
            return ""

        reason = f"{step['reason']}\n" if "reason" in step else ""
        number = "" if step["type"] == "text" else "all "
        instr = f"Use step-by-step reasoning to extract {number}{step['category']} from the document.\n"
        instr += f"Format the result in JSON:\n"
        prompt = f"{reason}{instr}"

        if step["type"] == "table":
            prompt_obj = "{\n"
            for column in step["columns"]:
                prompt_obj += (
                    f'          "{column.lower()}": "Description of the field",\n'
                )
            prompt_obj += "        },\n"
            prompt_obj += "        ...\n"

            prompt += """
            {
              "%s": [
                %s
              ]
            }
            """ % (
                step["category"],
                prompt_obj,
            )
            prompt += f"Use the following fields to describe the table: {', '.join(step['columns'])}\n"
        elif step["type"] == "list":
            prompt += """
                {
                  "%s": [
                    "description 1",
                    "description 2",
                    ...
                  ]
                }
                """ % (
                step["category"]
            )
        else:
            prompt += """
                {
                  "%s": "Description of the field"
                }
                """ % (
                step["category"]
            )

        prompt += '\nIf no %s %s found, return {"%s": []}.\n' % (
            step["category"],
            "is" if step["type"] == "text" else "are",
            step["category"],
        )

        prompt += "Your entire response/output is going to consist of a single JSON object {}, and you will NOT wrap it within JSON markdown markers."

        return prompt

    def __del__(self):
        """Ensure proper cleanup of resources."""
        if hasattr(self, "response_collector"):
            self.response_collector.close()
