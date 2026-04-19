import pytest
import uuid
from unittest.mock import MagicMock
from customer_support_agent.core.settings import Settings
from customer_support_agent.integrations.memory.langmem_store import CustomerMemoryStore

@pytest.fixture
def mock_settings():
    return Settings(
        google_api_key="mock_key",
        mem0_top_k=5
    )

@pytest.fixture
def memory_store(mock_settings):
    # We mock the LLM and the actual store internals if needed, 
    # but CustomerMemoryStore has a fallback to InMemoryStore which works without keys if we force it.
    mock_llm = MagicMock()
    store = CustomerMemoryStore(settings=mock_settings, llm=mock_llm)
    return store

def test_add_interaction(memory_store):
    user_id = f"test_user_{uuid.uuid4()}"
    memory_store.add_interaction(
        user_id=user_id,
        user_input="How do I file a claim?",
        assistant_response="You can file a claim via our portal."
    )
    
    # Search for it
    results = memory_store.search("file a claim", user_id=user_id)
    assert len(results) > 0
    assert "file a claim" in results[0]["memory"].lower()

def test_add_resolution(memory_store):
    user_id = f"test_user_{uuid.uuid4()}"
    memory_store.add_resolution(
        user_id=user_id,
        ticket_subject="Broken Windshield",
        ticket_description="Stone hit the glass on highway",
        accepted_draft="We will cover the windshield replacement minus deductible.",
        entity_links=["glass_repair"]
    )
    
    results = memory_store.search("windshield", user_id=user_id)
    assert len(results) > 0
    assert "resolution" in results[0]["metadata"].get("type", "")
    assert "windshield replacement" in results[0]["memory"]

def test_list_memories(memory_store):
    user_id = f"test_user_{uuid.uuid4()}"
    for i in range(3):
        memory_store.add_interaction(user_id, f"Input {i}", f"Response {i}")
        
    memories = memory_store.list_memories(user_id=user_id, limit=10)
    assert len(memories) >= 3

def test_namespace_label():
    label = CustomerMemoryStore._namespace_label("User@Email.com!")
    assert label == "user-email-com"
    assert " " not in label
