import json
import logging
import os
from pathlib import Path
from typing import Union

from se.modules.llama_analyzer import LlamaAnalyzer
from se.utils import load_prompt

logger = logging.getLogger("se.agent_controller")


class AgentController:
    def __init__(self, persist_dir: Union[str, Path], max_iterations=5):
        self.analyzer = LlamaAnalyzer(persist_dir=persist_dir)
        self.max_iterations = max_iterations
        self.analysis_result = {}
        self.steps = {}
        self.missing_data = {}

    def run(self, file: str):
        if not file or not os.path.exists(file):
            raise ValueError(f"File '{file}' does not exist.")

        logger.info("Start agent...")

        # Determine dynamic initial analysis steps.
        # This should be done only once for the initial analysis.
        #
        # The return value of this function will be in the following format:
        #
        # {
        #   'document_type': 'Purchase Agreement',
        #   'analysis_steps': [
        #     {
        #       'category': 'Category name',
        #       'applicable': True,
        #       'type': 'table',
        #       'columns': ['Column 1', 'Column 2'],
        #       'reason': 'Reason for this analysis step'
        #     },
        #     ...
        #   ]
        # }
        steps_are_valid = False
        for i in range(self.max_iterations):
            self.steps = self.analyzer.determine_analysis_steps(file=file)
            steps_are_valid = self._validate_analysis_steps(self.steps)
            if steps_are_valid:
                break

        if not steps_are_valid:
            logger.error("Unable to determine analysis steps")
            return None, None

        for i in range(self.max_iterations):
            if len(self.missing_data) > 0:
                missing_result = self.analyzer.analyze_text(
                    file=file,
                    # We already did the initial analysis,
                    # so we don't need to determine the steps again
                    steps={},
                    # Analysis incomplete. We need to prepare a prompt for missing data.
                    prompt=self._missing_data_prompt(),
                )

                logger.info("Analysis incomplete. Prepare a prompt for missing data...")
                self.analysis_result = self._merge_missing_to_analysis(missing_result)
            else:
                self.analysis_result = self.analyzer.analyze_text(
                    file=file,
                    steps=self.steps,
                )

            if self._is_analysis_complete():
                logger.info("Analysis complete.")
                break

        return self.analysis_result, self.steps

    def _is_analysis_complete(self):
        """Check if the analysis has all required fields."""
        if not self.analysis_result:
            # TODO: We need to handle this special case
            return False

        result = True
        categories = [s["category"] for s in self.steps["analysis_steps"]]
        missing_data = {}

        for k in categories:
            if k not in self.analysis_result:
                missing_data[k] = "is missing in analysis result"
                result = False
            elif not self.analysis_result[k]:
                missing_data[k] = "is empty in analysis result"
                logger.info(f"Category '{k}' {missing_data[k]}")
                result = False
                continue
            elif self.analysis_result[k] == "Unknown":
                missing_data[k] = "is Unknown in analysis result"
                logger.info(f"Field '{k}' {missing_data[k]}")
                result = False

        self.missing_data = missing_data
        return result

    def _missing_data_prompt(self) -> str:
        """Build a prompt for missing data."""
        categories = [s["category"] for s in self.steps["analysis_steps"]]
        analysis_categories = "document_type, " + ", ".join(categories)

        prompt = load_prompt(
            "missing_data",
            analysis_result=json.dumps(self.analysis_result, indent=2),
            analysis_categories=analysis_categories,
            missing_categories=", ".join(self.missing_data.keys()),
            missing_data=self.missing_data,
        )
        return prompt

    def _merge_missing_to_analysis(self, missing_result: dict) -> dict:
        """Merge missing data to the analysis result."""
        analysis = self.analysis_result.copy()
        if not missing_result or not missing_result["categories"]:
            logger.error("No missing data to merge to analysis result.")
            return analysis

        for category, items in missing_result.get("categories", {}).items():
            # Ensure the category exists in the analysis
            if category not in analysis:
                logger.debug(
                    f"Category '{category}' not found in analysis result, adding it..."
                )
                analysis[category] = []

            # Handle different item types
            if isinstance(items, list):
                # Append new items to the analysis, avoiding duplicates
                existing_items = {
                    tuple(item.items()) if isinstance(item, dict) else item
                    for item in analysis[category]
                }
                for item in items:
                    if isinstance(item, dict):
                        if tuple(item.items()) not in existing_items:
                            analysis[category].append(item)
                            existing_items.add(tuple(item.items()))
                    elif item not in existing_items:
                        analysis[category].append(item)
                        existing_items.add(item)

        return analysis

    def _validate_analysis_steps(self, data) -> bool:
        """Validate the structure of the analysis steps."""
        if not data or not isinstance(data, dict):
            logger.error("Analysis steps are not valid dictionary")
            return False

        # Check for document_type
        if (
            "document_type" not in data
            or not isinstance(data["document_type"], str)
            or not data["document_type"].strip()
        ):
            logger.error("Missing or invalid 'document_type'.")
            return False

        # Check for analysis_steps
        if (
            "analysis_steps" not in data
            or not isinstance(data["analysis_steps"], list)
            or not data["analysis_steps"]
        ):
            logger.error("Missing or invalid 'analysis_steps'.")
            return False

        # Validate each step in analysis_steps
        for i, step in enumerate(data["analysis_steps"]):
            if not isinstance(step, dict):
                logger.error(f"Analysis step at index {i} is not a dictionary.")
                return False

            if (
                "category" not in step
                or not isinstance(step["category"], str)
                or not step["category"].strip()
            ):
                logger.error(
                    f"Missing or invalid 'category' in analysis step at index {i}."
                )
                return False

            if "applicable" not in step or not isinstance(step["applicable"], bool):
                logger.error(
                    f"Missing or invalid 'applicable' in analysis step at index {i}."
                )
                return False

            if (
                "type" not in step
                or not isinstance(step["type"], str)
                or not step["type"].strip()
            ):
                logger.error(
                    f"Missing or invalid 'type' in analysis step at index {i}."
                )
                return False

            if step["type"] not in ["text", "list", "table"]:
                logger.error(
                    f"Invalid 'type' in analysis step at index {i}. Possible values are: 'text', 'list', 'table'."
                )
                return False

            if step["type"] == "table":
                if (
                    "columns" not in step
                    or not isinstance(step["columns"], list)
                    or not step["columns"]
                ):
                    logger.error(
                        f"Missing or invalid 'columns' in analysis step at index {i}."
                    )
                    return False

                if not all(
                    isinstance(col, str) and col.strip() for col in step["columns"]
                ):
                    logger.error(
                        f"Invalid column entries in analysis step at index {i}."
                    )
                    return False

            if (
                "reason" not in step
                or not isinstance(step["reason"], str)
                or not step["reason"].strip()
            ):
                logger.error(
                    f"Missing or invalid 'reason' in analysis step at index {i}."
                )
                return False

        return True
