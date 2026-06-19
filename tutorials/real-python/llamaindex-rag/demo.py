from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, load_index_from_storage
from dotenv import load_dotenv

load_dotenv()

##first attempt to load index from storage, if not found, create a new index and persist it to storage
try:
    storage_context = StorageContext.from_defaults(persist_dir="./data/storage")
    index = load_index_from_storage(storage_context)
    print("Index loaded from storage...")
except Exception as e:
    print("Index not found in storage, creating a new index...")
    reader = SimpleDirectoryReader(input_files=["./data/pep8.rst"])
    documents = reader.load_data()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir="./data/storage")
    print("Index created and persisted to storage...")


#reader = SimpleDirectoryReader(input_files=["./data/pep8.rst"])
#documents = reader.load_data()

#index = VectorStoreIndex.from_documents(documents)
#index.storage_context.persist(persist_dir="./data/storage")

query_engine = index.as_query_engine()
print(query_engine.query("What is this document about?"))
