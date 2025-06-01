import json
import logging
from datetime import datetime
from crm_agent import create_workflow, AgentState  # Import from crm_agent.py
from typing import TypedDict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define test cases
TEST_CASES = [
    {
        "id": "TC001",
        "query": "Create a contact for Luna Lovegood with email luna.lovegood.unique2025@example.com",
        "description": "Create contact with full details",
        "expected_operation": "create_contact"
    },
    {
        "id": "TC002",
        "query": "Create a contact for Neville Longbottom with email neville.longbottom.unique2025@example.com and phone 555-987-6543",
        "description": "Create contact with additional phone property",
        "expected_operation": "create_contact"
    },
    {
        "id": "TC003",
        # Use a valid existing contact ID or mock it accordingly
        "query": "Update contact ID 135708713670 with firstname Hermione",
        "description": "Update existing contact's firstname",
        "expected_operation": "update_contact"
    },
    {
        "id": "TC004",
        "query": "Create a deal named Magical Broomstick Sale for $7500",
        "description": "Create deal with name and amount",
        "expected_operation": "create_deal"
    },
    {
        "id": "TC005",
        "query": "Create a contact for Draco Malfoy with email draco.malfoy.unique2025@example.com",
        "description": "Create contact with unique email to avoid duplicates",
        "expected_operation": "create_contact"
    },
    {
        "id": "TC006",
        "query": "Update contact ID 135708713670 with email updated.email.unique2025@example.com",
        "description": "Update existing contact email",
        "expected_operation": "update_contact"
    },
    {
        "id": "TC007",
        "query": "Create a contact with email ginny.weasley.unique2025@example.com",
        "description": "Create contact with minimal details and unique email",
        "expected_operation": "create_contact"
    }
]


def save_results_to_txt(results, filename="test_results.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        for r in results:
            f.write(f"Test ID: {r['test_id']}\n")
            f.write(f"Description: {r['description']}\n")
            f.write(f"Query: {r['query']}\n")
            f.write(f"Expected Operation: {r['expected_operation']}\n")
            f.write(f"Actual Operation: {r['actual_operation']}\n")
            f.write(f"Success: {r['success']}\n")
            f.write(f"Timestamp: {r['timestamp']}\n")
            f.write(f"Result: {json.dumps(r['result'], indent=2)}\n")
            f.write("-" * 40 + "\n")

def run_tests():
    # Initialize workflow from crm_agent.py
    workflow = create_workflow()
    results = []

    # Run each test case
    for test in TEST_CASES:
        test_id = test["id"]
        query = test["query"]
        description = test["description"]
        expected_operation = test["expected_operation"]

        logger.info(f"Running test {test_id}: {description}")
        logger.info(f"Query: {query}")

        try:
            # Initialize state
            initial_state: AgentState = {"query": query}
            # Invoke workflow
            result = workflow.invoke(initial_state)
            
            # Log result
            logger.info(f"Result for {test_id}: {json.dumps(result, indent=2)}")
            
            # Validate operation
            operation = result.get("operation")
            is_success = (
                operation == expected_operation and
                result.get("email_status") == "sent" and
                not result.get("result", {}).get("error")
            ) if expected_operation else (operation is None)

            # Store test result
            test_result = {
                "test_id": test_id,
                "description": description,
                "query": query,
                "expected_operation": expected_operation,
                "actual_operation": operation,
                "result": result,
                "success": is_success,
                "timestamp": datetime.utcnow().isoformat()
            }
            results.append(test_result)

        except Exception as e:
            logger.error(f"Test {test_id} failed: {str(e)}")
            test_result = {
                "test_id": test_id,
                "description": description,
                "query": query,
                "expected_operation": expected_operation,
                "actual_operation": None,
                "result": {"error": str(e)},
                "success": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            results.append(test_result)

    # Save results to JSON file
    output_file = "test_results.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Test results saved to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save test results: {str(e)}")

    # Save results to TXT file
    try:
        save_results_to_txt(results)
        logger.info("Test results saved to test_results.txt")
    except Exception as e:
        logger.error(f"Failed to save test results to txt: {str(e)}")

    # Summarize results
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    logger.info(f"Test Summary: {passed_tests}/{total_tests} tests passed")

if __name__ == "__main__":
    run_tests()
