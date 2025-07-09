import json
import azure.functions as func
import logging
import agents

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Constants for the Azure Blob Storage container, file, and blob path
_SNIPPET_NAME_PROPERTY_NAME = "snippetname"
_SNIPPET_PROPERTY_NAME = "snippet"
_BLOB_PATH = "snippets/{mcptoolargs." + _SNIPPET_NAME_PROPERTY_NAME + "}.json"


class ToolProperty:
    def __init__(self, property_name: str, property_type: str, description: str):
        self.propertyName = property_name
        self.propertyType = property_type
        self.description = description

    def to_dict(self):
        return {
            "propertyName": self.propertyName,
            "propertyType": self.propertyType,
            "description": self.description,
        }


# Define the tool properties using the ToolProperty class
tool_properties_save_snippets_object = [
    ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The name of the snippet."),
    ToolProperty(_SNIPPET_PROPERTY_NAME, "string", "The content of the snippet."),
]

tool_properties_get_snippets_object = [ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The name of the snippet.")]

# Convert the tool properties to JSON
tool_properties_save_snippets_json = json.dumps([prop.to_dict() for prop in tool_properties_save_snippets_object])
tool_properties_get_snippets_json = json.dumps([prop.to_dict() for prop in tool_properties_get_snippets_object])

@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="get_aiagentdata",
    description="Retrieve data from ai agents.",    
    toolProperties=json.dumps([ {"propertyName": "query", "propertyType": "string", "description": "Whats the weather in Seattle today?"} ]),
)
def get_aiagentdata(context) -> str:
    """
    Retrieves a snippet by name from Azure Blob Storage.

    Args:
        file (func.InputStream): The input binding to read the snippet from Azure Blob Storage.
        context: The trigger context containing the input arguments.

    Returns:
        str: The content of the snippet or an error message.
    """
    # snippet_content = file.read().decode("utf-8")
    content = json.loads(context)
    query_from_args = content["arguments"].get("query", "") 
    datars = agents.ai_default_agent(query_from_args)
    print(f"Data returned from agent: {datars}")
    logging.info(f"Retrieved snippet: {datars}")
    return f"Hello, {datars}. This HTTP triggered function executed successfully."