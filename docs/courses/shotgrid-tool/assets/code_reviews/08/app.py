from dotenv import load_dotenv
import os

from griptape.artifacts import ListArtifact
from griptape.structures import Agent
from griptape.utils import Chat
from griptape.tools import DateTimeTool, VectorStoreTool
from griptape.drivers import (
    LocalVectorStoreDriver,
    OpenAiChatPromptDriver,
    OpenAiEmbeddingDriver,
)
from griptape.engines.rag import RagEngine
from griptape.engines.rag.modules import PromptResponseRagModule
from griptape.engines.rag.stages import ResponseRagStage
from griptape.loaders import WebLoader
from griptape.chunkers import TextChunker

# from reverse_string_tool import ReverseStringTool
from shotgrid_tool import ShotGridTool

load_dotenv()

# Create the vector database
vector_store_driver = LocalVectorStoreDriver(embedding_driver=OpenAiEmbeddingDriver())

# Create the query engine
rag_engine = RagEngine(
    response_stage=ResponseRagStage(
        response_modules=[PromptResponseRagModule(prompt_driver=OpenAiChatPromptDriver(model="gpt-4o-mini"))]
    ),
)

# API Documentation
shotgrid_api_urls = [
    "https://developers.shotgridsoftware.com/python-api/reference.html",
    "https://developers.shotgridsoftware.com/python-api/cookbook/usage_tips.html",
    "https://developers.shotgridsoftware.com/python-api/cookbook/attachments.html",
    "https://developers.shotgridsoftware.com/python-api/cookbook/tasks/updating_tasks.html",
    "https://developers.shotgridsoftware.com/python-api/cookbook/tasks/task_dependencies.html",
    "https://developers.shotgridsoftware.com/python-api/cookbook/tasks/split_tasks.html",
]

# Load the API documentation
artifacts = WebLoader().load_collection(shotgrid_api_urls)

# Convert to List Artifact
artifacts = ListArtifact(list(artifacts.values()))

# Chunk the documentation
artifacts = TextChunker().chunk(artifacts)

# Upsert documentation  into the vector database
namespace = "shotgrid_api"
vector_store_driver.upsert_text_artifacts({namespace: artifacts})


# Instantiate the Vector Store Tool
vector_store_tool = VectorStoreTool(
    description="Contains information about ShotGrid api. Use it to help with ShotGrid client requests.",
    vector_store_driver=vector_store_driver,
    query_params={"namespace": namespace},
    off_prompt=False,
)

SHOTGRID_URL = os.environ["SHOTGRID_URL"]
SHOTGRID_API_KEY = os.environ["SHOTGRID_API_KEY"]
SHOTGRID_SCRIPT = "Griptape API"
SHOTGRID_USER = os.environ["SHOTGRID_USER"]
SHOTGRID_PASSWORD = os.environ["SHOTGRID_PASSWORD"]


# Instantiate the tool
shotgrid_tool = ShotGridTool(
    base_url=SHOTGRID_URL,
    api_key=SHOTGRID_API_KEY,
    script_name=SHOTGRID_SCRIPT,
    user_login=SHOTGRID_USER,
    user_password=SHOTGRID_PASSWORD,
    login_method="user",
    off_prompt=False,
)

# Instantiate the agent
agent = Agent(
    tools=[
        DateTimeTool(off_prompt=False),
        shotgrid_tool,
        vector_store_tool,
        # ReverseStringTool(off_prompt=False),
    ],
    stream=True,
)


# Start chatting
Chat(agent).start()
